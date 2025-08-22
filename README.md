# LieOTAlign: A Differentiable Protein Structure Alignment Framework



This repository contains the official implementation of **LieOTAlign**, a novel and fully differentiable protein structure alignment framework built on the mathematical principles of Lie algebra and Optimal Transport (OT).

## Abstract

The comparison of protein structures is fundamental to understanding biological function and evolutionary relationships. Existing methods, while powerful, often rely on heuristic search algorithms and non-differentiable scoring functions, which limits their direct integration into end-to-end deep learning pipelines. This paper introduces LieOTAlign, a novel and fully differentiable protein structure alignment framework. LieOTAlign represents rigid body transformations within the Lie algebra of SE(3), which intrinsically preserves the geometric validity of rotations and translations during optimization. We formulate the alignment task as an optimal transport problem, seeking the most efficient mapping between two protein structures. This approach leads to a differentiable version of the TM-score, the Sinkhorn score, which is derived from the entropically regularized OT solution computed via the Sinkhorn algorithm. The entire LieOTAlign pipeline is differentiable, enabling the use of gradient-based optimizers like AdamW to maximize structural similarity. Benchmarking against the official TM-align on the RPIC dataset shows that LieOTAlign can identify longer, topologically significant alignments, achieving higher TM-scores.

## Key Features

- **Differentiable TM-score:** We replace the hard-to-optimize TM-score with a differentiable "Sinkhorn score" based on Optimal Transport, enabling gradient-based optimization.
- **Lie Algebra for Transformations:** Rigid body transformations (rotations and translations) are parameterized using the Lie algebra of SE(3). This guarantees that transformations are always geometrically valid, avoiding complex constraints during optimization.
- **End-to-End Differentiable:** The entire pipeline is differentiable, allowing for seamless integration into larger deep learning models.
- **Structure-Only Alignment:** The method relies solely on the 3D coordinates of protein structures, making it applicable to proteins with low sequence similarity.

## How It Works

1.  **Representing Transformation:** Instead of optimizing a 3x3 rotation matrix (9 values with constraints), we optimize a 3D vector `w` in the Lie algebra. The matrix exponential `R = exp(W)` guarantees a valid rotation matrix `R`. The full transformation is defined by a 6D vector (3 for rotation, 3 for translation).

2.  **Optimal Transport as Soft Alignment:** We treat the two sets of protein atoms (C-alphas) as two probability distributions. Instead of finding a "hard" one-to-one alignment, we use the Sinkhorn algorithm to compute a "soft" alignment matrix `P`. `P[i, j]` represents the probability that atom `i` in the mobile protein aligns with atom `j` in the reference protein.

3.  **Differentiable Scoring:** We define a similarity matrix `S` based on pairwise distances, similar to the TM-score formula. The final "Sinkhorn Score" is the sum of all similarities weighted by their alignment probabilities from the matrix `P`.
    ```
    Score = sum(P * S)
    ```
    This score is fully differentiable.

4.  **Optimization:** We use the AdamW optimizer to find the 6 transformation parameters that maximize the Sinkhorn Score over a few hundred iterations.

## Use 

python3 gemini_tm_align_final.py --mobile RPIC_all/d1nfn__.pdb --reference RPIC_all/d1he9a_.pdb --steps 5000 --cutoff 5.0 --output d1nfn___ligned0821.pdb

You can --help for more information. Enjoy it!


## email
Yue Hu
huyue@qlu.edu.cn
