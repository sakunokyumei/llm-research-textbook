"""Build tiny stand-in models for offline verification.

The verification sandbox cannot download from the Hugging Face Hub, so the
chapter code is run against tiny, randomly initialised models that have the
same architecture classes and tokenizer behaviour (chat template, special
tokens) as the real ones. This checks that the code *runs* with the real
APIs. It cannot check the quality of the real models' answers.
"""
from pathlib import Path
import json
import sys

from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
from transformers import (PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM,
                          GPT2Config, GPT2LMHeadModel, BertConfig, BertModel)

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
FAKES = CACHE / "fakes"

QWEN_TEMPLATE = (Path(__file__).parent / "qwen_chat_template.jinja").read_text(encoding="utf-8")


def corpus_lines():
    text = (CACHE / "downloads" / "soseki-sample.txt").read_text(encoding="utf-8")
    english = ("The quick brown fox jumps over the lazy dog. Hello world! "
               "Language models predict the next token. 1 2 3 4 5 6 7 8 9 0 + - * / = ( ) { } [ ] : , . \" '\n") * 50
    return text.splitlines() + english.splitlines()


def byte_bpe(vocab_size, specials):
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=specials,
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    tok.train_from_iterator(corpus_lines(), trainer=trainer)
    return tok


QWEN_SPECIALS = ["<|endoftext|>", "<|im_start|>", "<|im_end|>", "<|object_ref_start|>", "<|object_ref_end|>",
                 "<|box_start|>", "<|box_end|>", "<|quad_start|>", "<|quad_end|>", "<|vision_start|>",
                 "<|vision_end|>", "<|vision_pad|>", "<|image_pad|>", "<|video_pad|>", "<tool_call>",
                 "</tool_call>", "<|fim_prefix|>", "<|fim_middle|>", "<|fim_suffix|>", "<|fim_pad|>",
                 "<|repo_name|>", "<|file_sep|>"]
QWEN_PATTERN = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""


def qwen_tokenizer():
    """Qwen2/2.5 byte-level BPE rebuilt from the published qwen.tiktoken ranks.

    The rank file ships inside the `dashscope` wheel on PyPI (dashscope/resources/qwen.tiktoken);
    copy it to .cache/vocab/. Regular ids 0..151642 and special ids from 151643 match Qwen2.5.
    """
    from tokenizers import normalizers
    from transformers.convert_slow_tokenizer import TikTokenConverter
    vocab = CACHE / "vocab" / "qwen.tiktoken"
    if not vocab.exists():
        return byte_bpe(3000, QWEN_SPECIALS)
    tk = TikTokenConverter(vocab_file=str(vocab), pattern=QWEN_PATTERN).converted()
    tk.normalizer = normalizers.NFC()
    from tokenizers import AddedToken
    # like the real Qwen2.5 tokenizer: <tool_call> and the FIM/repo tokens are added but not "special",
    # so skip_special_tokens=True keeps them (ch23 parses <tool_call> from decoded text)
    not_special = QWEN_SPECIALS[QWEN_SPECIALS.index("<tool_call>"):]
    tk.add_tokens([AddedToken(t, special=t not in not_special, normalized=False) for t in QWEN_SPECIALS])
    tk.add_special_tokens([AddedToken(t, special=True, normalized=False) for t in QWEN_SPECIALS if t not in not_special])
    assert tk.token_to_id("<|im_start|>") == 151644 and tk.token_to_id("<|file_sep|>") == 151664
    return tk


def qwen(name):
    tok = PreTrainedTokenizerFast(tokenizer_object=qwen_tokenizer(),
                                  eos_token="<|im_end|>" if "Instruct" in name else "<|endoftext|>",
                                  pad_token="<|endoftext|>", unk_token=None)
    tok.chat_template = QWEN_TEMPLATE
    cfg = Qwen2Config(vocab_size=151936 if len(tok) > 151000 else len(tok), hidden_size=64, intermediate_size=128,
                      num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                      max_position_embeddings=2048, tie_word_embeddings=True,
                      eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id,
                      bos_token_id=None)
    model = Qwen2ForCausalLM(cfg)
    out = FAKES / name
    tok.save_pretrained(out)
    model.save_pretrained(out)
    (out / "generation_config.json").write_text(json.dumps(
        {"eos_token_id": tok.eos_token_id, "pad_token_id": tok.pad_token_id,
         "do_sample": True, "temperature": 0.7, "top_p": 0.8}), encoding="utf-8")


def gpt2():
    tok = PreTrainedTokenizerFast(tokenizer_object=byte_bpe(1500, ["<|endoftext|>"]),
                                  eos_token="<|endoftext|>", bos_token="<|endoftext|>",
                                  unk_token="<|endoftext|>")
    cfg = GPT2Config(vocab_size=len(tok), n_positions=1024, n_embd=64, n_layer=2, n_head=4,
                     bos_token_id=tok.eos_token_id, eos_token_id=tok.eos_token_id)
    out = FAKES / "gpt2"
    tok.save_pretrained(out)
    GPT2LMHeadModel(cfg).save_pretrained(out)


def e5():
    tok = PreTrainedTokenizerFast(tokenizer_object=byte_bpe(1500, ["[PAD]", "[UNK]", "[CLS]", "[SEP]"]),
                                  pad_token="[PAD]", unk_token="[UNK]", cls_token="[CLS]",
                                  sep_token="[SEP]", model_input_names=["input_ids", "attention_mask"])
    cfg = BertConfig(vocab_size=len(tok), hidden_size=32, num_hidden_layers=2,
                     num_attention_heads=2, intermediate_size=64, max_position_embeddings=512)
    out = FAKES / "multilingual-e5-small"
    tok.save_pretrained(out)
    BertModel(cfg).save_pretrained(out)


if __name__ == "__main__":
    FAKES.mkdir(parents=True, exist_ok=True)
    for name in ["Qwen2.5-0.5B-Instruct", "Qwen2.5-0.5B", "Qwen2.5-1.5B-Instruct"]:
        qwen(name)
    gpt2()
    e5()
    print("fakes ready:", sorted(p.name for p in FAKES.iterdir()), file=sys.stderr)
