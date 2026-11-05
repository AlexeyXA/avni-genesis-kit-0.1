# Product positioning — AVNI Genesis Kit 0.1

## Position

**Verified Agent Handoff:** a local-first CLI that packages a Python agent, restores it into a clean directory, checks its declared artifacts and acceptance behavior, and records lineage.

## Initial customer hypothesis

Small AI-automation studios and independent Python agent developers who deliver agents to customers or hand projects to another developer.

The hypothesized pain is not "I need another agent framework." It is "I need a reliable, reviewable handoff of an existing agent and a way to check that the recipient restored the declared version."

## Product boundary

AVNI does not replace:

- agent frameworks (LangGraph, OpenAI Agents SDK, CrewAI);
- evaluation/observability products (Langfuse, Braintrust);
- package/build systems (Nix, Bazel, Docker);
- supply-chain provenance standards (SLSA, in-toto).

AVNI's proposed value is to connect a portable agent description, allowlisted artifacts, package/restore procedure, acceptance evidence and lineage in one small workflow.

## Defensible claim for MVP 0.1

For the included deterministic, dependency-free Python example, AVNI can:

1. create a genome and artifact hashes;
2. build a deterministic package;
3. restore it offline in a new directory;
4. assign a new child organism ID while preserving genome ID;
5. verify the declared acceptance cases;
6. compare outputs with the parent;
7. preserve a locally verifiable lineage chain;
8. optionally sign the verification report with Ed25519.

Do not generalize this claim to arbitrary AI systems or production environments.
