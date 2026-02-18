# Contract: Skill Capability Manifest

Doc: `docs/contracts/skill_capability_manifest.md`  
Date: 2026-02-18  
Status: Draft (v0)

## Purpose

Define a typed capability declaration format for each tool/skill.

## Required Fields Per Capability

- `action_class` (string, unique)
- `effect_class` (`none`, `reversible`, `privileged`, `destructive`)
- `requires_consent` (boolean)
- `allowed_scopes` (list of strings)
- `required_verifiers` (list of verifier labels)
- `provenance_bindings` (list of required provenance keys)

## JSON Example

```json
{
  "capabilities": [
    {
      "action_class": "SEND_EMAIL",
      "effect_class": "privileged",
      "requires_consent": true,
      "allowed_scopes": ["mailbox:primary"],
      "required_verifiers": ["scope_verifier", "consent_verifier"],
      "provenance_bindings": ["model_call_id", "prompt_hash", "input_provenance"]
    }
  ]
}
```

## Verifier Contract

Before action release, verifier must ensure:

1. Action exists in manifest.
2. Requested scope is allowed.
3. Consent requirements are satisfied.
4. Required provenance fields are present.
5. RC posture-specific restrictions are applied.

