import unittest
import torch
from contrastive import pair_loss, sequence_masks


class ContrastiveTests(unittest.TestCase):
    def test_positive_identical_and_negative_identical(self):
        h = torch.tensor([[[1., 0.], [1., 0.]]])
        a, b = torch.tensor([[True, False]]), torch.tensor([[False, True]])
        self.assertAlmostEqual(pair_loss(h,a,b,torch.tensor([0])).item(),0)
        self.assertAlmostEqual(pair_loss(h,a,b,torch.tensor([1])).item(),1)

    def test_negative_orthogonal_and_opposite(self):
        a, b = torch.tensor([[True, False]]), torch.tensor([[False, True]])
        for second in ([0.,1.],[-1.,0.]):
            h=torch.tensor([[[1.,0.],second]])
            self.assertEqual(pair_loss(h,a,b,torch.tensor([1])).item(),0)

    def test_padding_ignored_and_batch_mean(self):
        h=torch.tensor([[[1.,0.],[0.,1.],[999.,999.]],[[1.,0.],[1.,0.],[999.,999.]]])
        a=torch.tensor([[True,False,False]]*2); b=torch.tensor([[False,True,False]]*2)
        self.assertAlmostEqual(pair_loss(h,a,b,torch.tensor([0,1])).item(),1)

    def test_gradient_direction(self):
        for label, sign in ((0,-1),(1,1)):
            h=torch.tensor([[[1.,0.],[1.,1.]]],requires_grad=True)
            a,b=torch.tensor([[True,False]]),torch.tensor([[False,True]])
            loss=pair_loss(h,a,b,torch.tensor([label])); loss.backward()
            self.assertTrue(torch.isfinite(h.grad).all())
            self.assertEqual(int(torch.sign(h.grad[0,1,0])),sign)

    def test_empty_and_overlapping_masks_rejected(self):
        h=torch.ones(1,2,2); a=torch.tensor([[True,False]]); z=torch.zeros_like(a)
        for b in (a,z):
            with self.assertRaises(ValueError): pair_loss(h,a,b,torch.tensor([0]))

    def test_special_token_masks(self):
        class Encoding(dict):
            def sequence_ids(self,i): return [None,0,0,None,1,None]
        a,b=sequence_masks(Encoding(input_ids=[[0]*6]))[0]
        self.assertEqual(a,[False,True,True,False,False,False])
        self.assertEqual(b,[False,False,False,False,True,False])

if __name__ == '__main__': unittest.main()
