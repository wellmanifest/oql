# Wellmanifest OQL

Standard używania OQL jako źródła konfiguracji dla aplikacji, urządzeń,
aktualizacji firmware i wdrożeń obejmujących wiele urządzeń.

Experimental **0.1.0**. HOME `wellmanifest`; runtime stays in adopting projects.

- [Standard: contexts, ownership, firmware and fleet lifecycle](docs/information/oql-lifecycle-standard.md)
- [Canonical rule catalog](policy.json): 26 requirements
- [Closed rollout review schema](schemas/rollout-review.schema.json)
- [Synthetic network plan](examples/network-rollout.json) and [firmware plan](examples/firmware-rollout.json)
- [Documentation index](docs/README.md)
- [Maskservice source audit](https://github.com/subactor/docs/blob/main/architecture/analysis/maskservice-oql-adoption.md) — separate owner; consult delivery state before treating the link as published

Python 3.11+ and `jsonschema` 4.x:

```sh
python3 -m unittest discover -s tests -v
python3 operations/conformance.py examples/network-rollout.json
python3 operations/conformance.py examples/firmware-rollout.json
```

The checker is offline and read-only. It checks declared schema and cross-field
consistency; it does not parse OQL, verify signatures, authorize changes, contact
hardware, install firmware or prove production conformance. Evidence references
are not followed. Standard adoption is explicit and pinned, never automatic.

Update `policy.json` first when changing normative rules and keep the reference
text synchronized. Changes in rule meaning, schema or compatibility require a
versioned migration and refreshed manifest digests.
