"""REINFORCE on two synthetic Bernoulli arms, with a lagged reward baseline."""
import torch


def experiment(seed, steps=1000):
    rng = torch.Generator().manual_seed(seed)
    logits = torch.zeros(2, requires_grad=True)
    optimizer = torch.optim.SGD([logits], lr=0.05)
    baseline, total = 0.0, 0
    for _ in range(steps):
        probs = logits.softmax(0)
        action = torch.multinomial(probs.detach(), 1, generator=rng).item()
        reward = float(torch.rand((), generator=rng) < [0.2, 0.8][action])
        loss = -(reward - baseline) * probs[action].log()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        baseline = 0.95 * baseline + 0.05 * reward
        total += reward
    return {"seed": seed, "probability_good_arm": logits.softmax(0)[1].item(),
            "average_training_reward": total/steps}


if __name__ == "__main__":
    torch.set_num_threads(1)
    for seed in range(3):
        print(experiment(seed))
