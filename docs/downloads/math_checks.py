"""Check numerical claims with independent formulations (CPU)."""
import math
import torch


def online_weighted_sum(scores, values):
    maximum, denominator, numerator = -math.inf, 0.0, 0.0
    for s, v in zip(scores, values):
        newmax = max(maximum, s)
        scale = math.exp(maximum - newmax)
        numerator = numerator * scale + math.exp(s - newmax) * v
        denominator = denominator * scale + math.exp(s - newmax)
        maximum = newmax
    return numerator / denominator


def main():
    x = torch.tensor([1000., 1001., 999.], dtype=torch.float64)
    v = torch.tensor([2., 7., -1.], dtype=torch.float64)
    expected = (x.softmax(0) * v).sum().item()
    assert abs(online_weighted_sum(x.tolist(), v.tolist()) - expected) < 1e-12
    z = torch.tensor(1.3, dtype=torch.float64, requires_grad=True)
    f = lambda a: a ** 3 + torch.sin(a)
    f(z).backward()
    h = 1e-5
    finite = ((f(z.detach() + h) - f(z.detach() - h)) / (2*h)).item()
    assert abs(z.grad.item() - finite) < 1e-8
    # W is frozen; BA is the only trainable change. B=0 initially means grad(A)=0.
    torch.manual_seed(0)
    w = torch.randn(3, 4, requires_grad=False)
    a = torch.randn(2, 4, requires_grad=True)
    b = torch.zeros(3, 2, requires_grad=True)
    inp = torch.randn(5, 4)
    (inp @ (w + b @ a).T).square().mean().backward()
    assert w.grad is None and torch.count_nonzero(a.grad) == 0
    assert torch.count_nonzero(b.grad) > 0
    print({"online_softmax": expected, "derivative": z.grad.item(),
           "finite_difference": finite, "lora_gradient_check": "passed"})


if __name__ == "__main__":
    main()
