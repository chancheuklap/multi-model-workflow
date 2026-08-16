# CONTEXT.md Format

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
{A one or two sentence description of the term}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.

## Single vs multi-context repos

**Single context (most repos):** One `CONTEXT.md` at the repo root. Maintain it with the structure above.

**Multiple contexts:** A Context Map at the repo root lists the contexts, where each leaf lives, and how they relate. `mmw domain path` prints which shape this repo is.

The Contexts table has three columns. The header row is exactly `Context`, `Leaf`, `Owns`. Each Leaf cell is one Markdown link, relative to the map, targeting a `.md` file under the context directory from `mmw domain dirs`. Owns is a non-empty ownership sentence. Relationships is a natural-language list. Leave the managed rules block as `mmw domain map-init` or `mmw domain sync` wrote it; fill only Contexts and Relationships.

```md
# Context Map

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| Ordering | [Ordering](./docs/context/ordering.md) | Receives and tracks customer orders; defines Customer. |
| Billing | [Billing](./docs/context/billing.md) | Generates invoices and processes payments. |
| Fulfillment | [Fulfillment](./docs/context/fulfillment.md) | Manages warehouse picking and shipping. |

## Relationships

- Ordering emits `OrderPlaced` events. Fulfillment consumes them and starts picking.
- Fulfillment emits `ShipmentDispatched` events. Billing consumes them and generates invoices.
- Ordering defines Customer. Billing uses an authoritative reference to Ordering's definition.
```

The `./docs/context/` links show relative-link form. Each leaf's real path must sit in the context directory from `mmw domain dirs`.

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.

## Authoritative references

A shared term is defined in one leaf. Other leaves cite that definition in this form:

```md
**Customer**:
(authoritative: [Customer](./ordering.md))
```

The path is relative to the current leaf. The target must be a leaf already registered on this Context Map.
