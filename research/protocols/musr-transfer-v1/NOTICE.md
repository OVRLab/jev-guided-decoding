# MuSR source attribution

MuSR is by Zayne Sprague, Xi Ye, Kaj Bostrom, Swarat Chaudhuri and Greg Durrett:
[paper](https://arxiv.org/abs/2310.16049),
[project](https://zayne-sprague.github.io/MuSR/).

The [Hugging Face dataset](https://huggingface.co/datasets/TAUR-Lab/MuSR)
at revision `7c365b439a222150f317764d4f16ae6c96d7d94a` declares
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Its pinned card is preserved unmodified in [README.dataset.md](README.dataset.md)
(SHA-256 `793154678fbec10387b116b4e4431cc05b1e44b49a79f030d7513a430c4d304e`).

Original author JSON metadata come from [the source repository](https://github.com/Zayne-sprague/MuSR)
at `b1f4d4168a9cfc6760e8b74d728e4516023dfaa5`. Its original
[MIT license notice](LICENSE.author.txt), including the 2024 Zayne Sprague copyright,
is preserved without modification (SHA-256
`2c8e2a28ca013557c73dff03ab3055b76f226dbeb8daa20dc36caeefe76f7946`).
The project's own license does not replace these upstream terms.

Our source CSV/JSON copies are unchanged. Derived case files rename fields, extract
numbered choices, separate reference labels, and assign project exposure/group
metadata. Study prompts, generated outputs, readout and analysis are our research
additions; they are not the author's official evaluator or an endorsement by the
authors. Preserve this notice with redistributed inputs and derivative records.

Implementation plan: bind all three notice files into the prospective R32a source
inventory and copy them into each frozen input bundle before any execution. Verify
the exact notice bytes alongside cases and checkpoints. A freeze regression must
first demonstrate the missing notices, then check that edits are rejected even
when a local file-inventory hash is recomputed. This changes packaging only; the
running R31 study and already archived v1 readability result remain untouched.
