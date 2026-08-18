# Excessive claims

> **这页管什么**：别做无法核实的断言：最快、最好、永远、保证。
>
> 来源：<https://developers.google.com/style/excessive-claims> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Words to avoid

- Superlatives: *best*, *simplest*, *fastest*, *never*, *always*.
- Certainty words: *ensure*, *guarantee* — usable only when something can truly be ensured or guaranteed.

## What counts as an excessive claim

A statement that:

- Makes a claim about performance or cost that isn't easily verifiable with data available to the reader.
- Makes a claim about security that would be invalidated by a security incident.
- Might be read as subjective or disparaging, especially about third-party products.

## Why

- Claims must hold not only today but account for what might be true in the future.
- Security claims are risky: documentation is invalid and not credible if someone compromises the product.
- Competitive claims may become untrue if you misread how the product works, or when the other company ships a new release.

## Alternatives

- For security, prefer "helps with security" or "is designed for security" — still true after an incident.
- For performance and competitive claims, cite sources rather than asserting superiority.

## Overall

Write factually and objectively, limited to verifiable information that will be true over the lifespan of the documentation.

## MMW note

This page targets outward-facing product claims. It is **not** a reason to soften hard constraints inside a skill — an MMW rule that says "never" is a guardrail, not a marketing claim.
