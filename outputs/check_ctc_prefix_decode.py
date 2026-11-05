"""Check prefix probabilities against exhaustive CTC path enumeration."""
import itertools,unittest
import numpy as np
from ctc_prefix_decode import decode


def collapse(path):
    return tuple(c for c,_ in itertools.groupby(path) if c)


class DecoderTest(unittest.TestCase):
    def test_exhaustive(self):
        rng=np.random.default_rng(42)
        for steps in range(1,5):
            for _ in range(8):
                probabilities=rng.dirichlet(np.ones(3),size=steps)
                scores={}
                for path in itertools.product(range(3),repeat=steps):
                    label=collapse(path)
                    scores[label]=scores.get(label,0)+np.prod([probabilities[t,c] for t,c in enumerate(path)])
                expected=max(scores,key=scores.get)
                self.assertEqual(decode(np.log(probabilities),width=100),expected)

    def test_repeat_requires_blank(self):
        p=np.array([[.01,.99],[.99,.01],[.01,.99]])
        self.assertEqual(decode(np.log(p)),(1,1))
        self.assertEqual(decode(np.log([[.01,.99],[.01,.99]])),(1,))

    def test_invalid_width(self):
        with self.assertRaises(ValueError):decode(np.log([[.5,.5]]),0)


if __name__=='__main__':unittest.main()
