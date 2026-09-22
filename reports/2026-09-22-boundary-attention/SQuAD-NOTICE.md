# SQuAD2.0-derived data attribution

R18 uses selected questions and full Wikipedia-derived paragraphs from the official
[SQuAD2.0 public development file](https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json).
The [dataset website](https://rajpurkar.github.io/SQuAD-explorer/) distributes the
data under [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Credit Pranav Rajpurkar, Robin Jia and Percy Liang, “Know What You Don't Know:
Unanswerable Questions for SQuAD,” ACL 2018, and the contributing Wikipedia authors.
[Paper](https://aclanthology.org/P18-2124/). Upstream question IDs, article titles and
paragraph IDs are retained for attribution and reconstruction. The source SHA-256
is `80a5225e94905956a6446d296ca1093975c4d3b3260f1d6c8f68bc2ab77182d8`.

Changes: article-disjoint project splits, deterministic class-balanced subset
selection, one question per paragraph, sentence source IDs, shared QA framing,
Granite-generated answers, Jev source relevance and research evaluation metadata.
The complete selected paragraph is preserved; sentence source text concatenates
back to its original bytes. Natural abstention grading is an explicitly disclosed
adaptation, not the official hidden-test evaluation or a leaderboard result.

SQuAD-derived fixtures, prompts and traces are shared under CC BY-SA 4.0. The
repository's software license does not replace that data license, relicense model
weights, or imply endorsement by Stanford, the dataset authors, Wikipedia or TypeSafe.
