#for some reason I am now unable to import aidungeon/gpt2generator.py so this will replace it for testing
import json
import os
from pathlib import Path
from typing import Union

import torch
import torch.nn.functional as F
import re
from transformers import GPT2Tokenizer, GPT2LMHeadModel, GPTNeoForCausalLM

import logging
logger = logging.getLogger(__name__)

# warnings.filterwarnings("ignore")
MODEL_CLASSES = {
    "gpt2": (GPT2LMHeadModel, GPT2Tokenizer),
    #"gpt2-experimental": (GPT2LMHeadModelExperimental, GPT2Tokenizer),
}


def getTokens(tokenizer, l):
    tokenizer.encode()


# the tokenizer does not preserve white space at the front of the string.
# so we will append something else to the front of the string and then remove it after tokenization
def hackyEncode(tokenizer, s):
    return tokenizer('====\n ' + s, verbose=False).input_ids[2:]


def memory_merge(prompt, context, tokenizer, maxHistory=1024):
    assert (prompt + context)
    # print(prompt+context)
    # logger.debug('RAW TEXT INPUT IS:`%r`', context)
    # the tokenizer is kind of broken for the first input, especially if it includes white space. Same with any trailing white space on the last output.
    # I'm going with the add prefix option but I'm not sure it's quite right
    prompt_tokens = tokenizer.encode(prompt, add_special_tokens=False, add_prefix_space=True)
    if len(prompt_tokens) >= maxHistory:
        logger.debug("Clamping the amount of prompt tokens.")
        context_tokens = prompt_tokens[-maxHistory:]
    else:
        context_tokens = hackyEncode(tokenizer, context)
        context_tokens = context_tokens[-(maxHistory - len(prompt_tokens)):]
        # logger.debug('DECODED CONTEXT TOKENS: `%r`', tokenizer.convert_ids_to_tokens(context_tokens))
        prompt_tokens.extend(context_tokens)
        context_tokens = prompt_tokens
        # logger.debug('DECODED OUTPUT IS: `%r`', tokenizer.decode(context_tokens, clean_up_tokenization_spaces=False))
        # this is a hack and it should be up to the sampler to deal with max size
        if len(context_tokens) > maxHistory:
            logger.error("CONTEXT IS TOO LONG ERROR")
            context_tokens = context_tokens[-maxHistory:]
    return context_tokens


def top_k_top_p_filtering(logits, top_k=0, top_p=0.0, filter_value=-float("Inf")):
    """ Filter a distribution of logits using top-k and/or nucleus (top-p) filtering
        Args:
            logits: logits distribution shape (batch size x vocabulary size)
            top_k > 0: keep only top k tokens with highest probability (top-k filtering).
            top_p > 0.0: keep the top tokens with cumulative probability >= top_p (nucleus filtering).
                Nucleus filtering is described in Holtzman et al. (http://arxiv.org/abs/1904.09751)
        From: https://gist.github.com/thomwolf/1a5a29f6962089e871b94cbd09daf317
    """
    top_k = min(top_k, logits.size(-1))  # Safety check
    if top_k > 0:
        # Remove all tokens with a probability less than the last token of the top-k
        indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[indices_to_remove] = filter_value

    if top_p > 0.0:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_indices_to_remove = cumulative_probs > top_p
        # Shift the indices to the right to keep also the first token above the threshold
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        # scatter sorted tensors to original indexing
        indices_to_remove = sorted_indices_to_remove.scatter(
            dim=-1, index=sorted_indices, src=sorted_indices_to_remove
        )
        logits[indices_to_remove] = filter_value
    return logits


# length should be max length, other settings should be removed, device should not be set
# we could possibly optimize this by having larger batch sizes but it would likely double or more the memory requirements
def sample_sequence(
        model,
        length,
        context,
        temperature=1,
        top_k=0,
        top_p=0.9,
        repetition_penalty=1.0,
        repetition_penalty_range=512,
        repetition_penalty_slope=3.33,
        top_p_first=True,
        device="cpu",
        stop_tokens=None,
        tokenizer=None
):
    """Actually generate the tokens"""
    logger.debug(
        f'temp: {temperature}    top_k: {top_k}    top_p: {top_p}    rep-pen: {repetition_penalty}    rep-pen-range: {repetition_penalty_range}    rep-pen-slope: {repetition_penalty_slope}'
    )
    context_tokens = context
    context = torch.tensor(context, dtype=torch.long, device=device)
    # context = context.repeat(num_samples, 1)
    generated = context
    USE_PAST = True
    next_token = context
    pasts = None
    clines = 0

    penalty = None
    if (
        repetition_penalty_range is not None
        and repetition_penalty_slope is not None
        and repetition_penalty_range > 0
    ):
        penalty = (torch.arange(repetition_penalty_range)/(repetition_penalty_range - 1)) * 2. - 1
        penalty = (repetition_penalty_slope * penalty) / (1 + torch.abs(penalty) * (repetition_penalty_slope - 1))
        penalty = 1 + ((penalty + 1) / 2) * (repetition_penalty - 1)

    with torch.no_grad():
        for j in range(length):
            # why would we ever not use past?
            # is generated and next_token always same thing?
            if not USE_PAST:
                input_ids_next = generated
                pasts = None
            else:
                input_ids_next = next_token

            # Note: we could also use 'past' with GPT-2/Transfo-XL/XLNet/CTRL (cached hidden-states)
            model_kwargs = {"past": pasts, "use_cache": True}
            model_inputs = model.prepare_inputs_for_generation(generated.unsqueeze(0), **model_kwargs)
            model_outputs = model(**model_inputs, return_dict=True)
            logits, pasts = model_outputs.logits, model_outputs.past_key_values
            logits = logits[0, -1, :].float()

            # Originally the order was Temperature, Repetition Penalty, then top-k/p
            if top_p_first:
                logits = top_k_top_p_filtering(logits, top_k=top_k, top_p=top_p)

            logits = logits / (temperature if temperature > 0 else 1.0)

            # repetition penalty from CTRL (https://arxiv.org/abs/1909.05858) plus range limit
            if repetition_penalty != 1.0:
                if penalty is not None:
                    penalty_len = min(generated.shape[0], repetition_penalty_range)
                    penalty_context = generated[-repetition_penalty_range:]
                    score = torch.gather(logits, 0, penalty_context)
                    penalty = penalty.type(score.dtype).to(score.device)
                    penalty_window = penalty[-penalty_len:]
                    score = torch.where(score < 0, score * penalty_window, score / penalty_window)
                    logits.scatter_(0, penalty_context, score)
                else:
                    score = torch.gather(logits, 0, generated)
                    score = torch.where(score < 0, score * repetition_penalty, score / repetition_penalty)
                    logits.scatter_(0, generated, score)

            if not top_p_first:
                logits = top_k_top_p_filtering(logits, top_k=top_k, top_p=top_p)

            if temperature == 0:  # greedy sampling:
                next_token = torch.argmax(logits, dim=-1).unsqueeze(-1)
            else:
                next_token = torch.multinomial(
                    F.softmax(logits, dim=-1), num_samples=1
                )
            generated = torch.cat((generated, next_token), dim=-1)
            # Decode into plain text
            o = generated[len(context_tokens):].tolist()
            generated.text = tokenizer.decode(
                o, clean_up_tokenization_spaces=False, skip_special_tokens=True
            )
            if (
                    (stop_tokens is not None)
                    and (j > 4)
                    and (next_token[0] in stop_tokens)
            ):
                # Why the minimum tokens, j>X. Because sometimes the models starts with whitespace, which will strip away anyway. Having a minimum amount of tokens before we stop usually means we don't just stop because of "\n " or similar
                logger.debug(
                    "Stopping generation as we found stop tokens. One of `%s`, in '%s'. token generated `%s`",
                    stop_tokens,
                    next_token,
                    j,
                )
                break
    #clear_lines(clines)
    return generated

def truncate_multiple_sequences(seqs, max_len=100):
    """Truncate multiple sequences, longest first, removing first."""
    while sum(len(s) for s in seqs) > max_len:
        longest = sorted(seqs, key=len, reverse=True)[0]
        longest.pop(0)


class GPT2Generator:
    def __init__(
            self, generate_num=60, temperature=0.4, top_k=40, top_p=0.9, dtype=torch.float32,
            model_path: Union[str, Path] = Path('models', 'pytorch-gpt2-xl-aid2-v5'), repetition_penalty=1, repetition_penalty_range=512, repetition_penalty_slope=3.33, max_history_tokens=1024
    ):
        self.generate_num = generate_num
        self.temp = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.top_p_first = True
        self.samples = 1
        self.dtype = dtype
        self.repetition_penalty = repetition_penalty
        self.repetition_penalty_range = repetition_penalty_range
        self.repetition_penalty_slope = repetition_penalty_slope
        self.batch_size = 1
        self.max_history_tokens = max_history_tokens - generate_num
        self.stop_token = "<|endoftext|>"

        if isinstance(model_path, str):
            self.checkpoint_path = model_path
            logger.warning(
                #f"Using DEBUG MODE! This will load one of the generic (non-finetuned) GPT2 models. "
                f"Selected: {model_path}")
        elif isinstance(model_path, Path):
            self.checkpoint_path = model_path
            if not self.checkpoint_path.exists():
                raise FileNotFoundError(
                    f"Could not find {str(self.checkpoint_path)} Make sure to download a pytorch model and put it in the models directory!"
                )
        else:
            raise ValueError(f"model_path must be either str or Path, got {type(model_path)}")

        self.device = torch.device("cuda" if self.dtype == torch.float16 else "cpu")
        logger.info(
            f"Using device={self.device}, checkpoint={str(self.checkpoint_path)}, dtype={self.dtype}"
        )

        # Load tokenizer and model
        model_class, tokenizer_class = MODEL_CLASSES["gpt2"]

        # Checking 3 places to see if it's a gpt-neo model
        with open(os.path.join(str(model_path), "config.json")) as f:
            model_config = json.load(f)
        neo_in_path = "gpt-neo" in str(model_path).lower()
        neo_in_architectures = "architectures" in model_config and "GPTNeoForCausalLM" in model_config["architectures"]
        neo_in_model_type = (
            "model_type" in model_config
            and model_config["model_type"] == "gpt_neo"
        )
        logger.info(
            f"Looking for GPT-Neo - path:{neo_in_path}, arch:{neo_in_architectures}, type:{neo_in_model_type}"
        )

        if neo_in_path or neo_in_architectures or neo_in_model_type:
            self.max_history_tokens = settings.getint("history-gpt-neo") - generate_num
            model_class = GPTNeoForCausalLM

        logger.info(f"Max token history: {str(self.max_history_tokens)}")

        self.tokenizer = tokenizer_class.from_pretrained(str(self.checkpoint_path))
        self.model = model_class.from_pretrained(str(self.checkpoint_path))
        self.model.to(self.dtype).to(self.device)
        self.model.eval()

    def sample_sequence(
            self, context_tokens=None, top_k=None, top_p=None, repetition_penalty=None, generate_num=None,
            temperature=None, stop_tokens=None, repetition_penalty_range=None, repetition_penalty_slope=None
    ):
        assert (top_k is not None)
        assert (temperature is not None)
        assert (top_p)
        assert (repetition_penalty)
        generate_num = generate_num if (generate_num is not None) else self.generate_num
        temperature = temperature if (temperature is not None) else self.temp
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repetition_penalty = repetition_penalty if repetition_penalty is not None else self.repetition_penalty
        repetition_penalty_range = repetition_penalty_range if repetition_penalty_range is not None else self.repetition_penalty_range
        repetition_penalty_slope = repetition_penalty_slope if repetition_penalty_slope is not None else self.repetition_penalty_slope
        length = len(context_tokens) + generate_num

        return sample_sequence(
            model=self.model,
            context=context_tokens,
            length=generate_num,
            # context=self.context,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            repetition_penalty_range=repetition_penalty_range,
            repetition_penalty_slope=repetition_penalty_slope,
            device=self.device,
            stop_tokens=stop_tokens,
            tokenizer=self.tokenizer,
            top_p_first=self.top_p_first
            # batch_size=self.batch_size,
        )

    def result_replace(self, result, allow_action=False):
        # logger.debug("BEFORE RESULT_REPLACE: `%s`", repr(result))

        #result = cut_trailing_sentence(result, allow_action=allow_action)

        if len(result) == 0:
            return ""
        first_letter_capitalized = result[0].isupper()
        result = result.replace('."', '".')
        result = result.replace("#", "")
        result = result.replace("*", "")
        # TODO look at this I think blank lines should be fine or blacklisted at generation time
        result = result.replace("\n\n", "\n")
        # result = first_to_second_person(result)

        if not first_letter_capitalized:
            result = result[0].lower() + result[1:]

        # this is annoying since we can already see the AIs output
        # logger.debug( "AFTER RESULT_REPLACE: `%r`. allow_action=%r", repr(result), allow_action)

        return result

    def generate_raw(
            self, context, prompt='', generate_num=None, temperature=None, top_k=None, top_p=None,
            repetition_penalty=None, repetition_penalty_range=512, repetition_penalty_slope=3.33, stop_tokens=None
    ):
        assert (top_k is not None)
        assert (temperature is not None)
        assert (top_p)
        assert (repetition_penalty)

        context_tokens = memory_merge(prompt, context, self.tokenizer, self.max_history_tokens)

        logger.debug(
            "Text passing into model `%r`",
            self.tokenizer.decode(
                context_tokens,
                clean_up_tokenization_spaces=True,
                # skip_special_tokens=True,
            ),
        )
        text = ""
        for _ in range(self.samples // self.batch_size):
            out = self.sample_sequence(
                context_tokens,
                generate_num=generate_num,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                repetition_penalty_range=repetition_penalty_range,
                repetition_penalty_slope=repetition_penalty_slope,
                stop_tokens=stop_tokens,
            )
            text += out.text
            # disabled clean up of spaces, see what effect this has TODO
            if self.stop_token:
                index = text.find(self.stop_token)
                if index == -1:
                    index = None
                text = text[:index]
            if stop_tokens is not None:
                for stop_token in stop_tokens:
                    index = text.find(self.stop_token)
                    if index == -1:
                        index = None
                    text = text[:index]
        return text

    def generate(self, context, prompt='', temperature=None, top_p=None, top_k=None, repetition_penalty=None, repetition_penalty_range=512, repetition_penalty_slope=3.33, depth=0):
        assert (top_k is not None)
        assert (temperature is not None)
        assert (top_p)
        assert (repetition_penalty)
        # logger.debug("BEFORE PROMPT_REPLACE: `%r`", prompt)

        # prompt = [self.prompt_replace(p) for p in prompt]

        # logger.debug("AFTER PROMPT_REPLACE is: `%r`", repr(prompt))
        assert (prompt + context)

        text = self.generate_raw(
            context, prompt, temperature=temperature, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, repetition_penalty_range=repetition_penalty_range, repetition_penalty_slope=repetition_penalty_slope,
            stop_tokens=None
        )

        logger.debug("Generated result is: `%r`", repr(text))

        result = self.result_replace(text)

        if (depth > 6) and len(result) == 0:
            # Sometimes it keeps generating a story startng with an action (">"), if it's tried a few times and it keeps
            # happening, lets let it keep action text which starts in ">"
            # We could just blacklist that token and force it to generate something else. TODO
            result = self.result_replace(text, allow_action=True)
            logger.info(
                "Model generated empty text after formatting `%r`. Trying to format less with allow_action=True. `%r`",
                text,
                result,
            )

            # same here as above
        if len(result) == 0:
            if depth < 20:
                logger.info("Model generated empty text trying again %r", depth)
                return self.generate(
                    prompt, context, temperature=temperature, top_p=top_p, top_k=top_k,
                    repetition_penalty=repetition_penalty, repetition_penalty_range=repetition_penalty_range, repetition_penalty_slope=repetition_penalty_slope, depth=depth + 1
                )
            else:
                logger.warn(
                    "Model generated empty text %r times. Try another action", depth
                )
        return result
