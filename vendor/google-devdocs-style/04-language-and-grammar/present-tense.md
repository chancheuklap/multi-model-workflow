# Present tense

> **这页管什么**：用现在时；will 和 would 什么时候才允许。
>
> 来源：<https://developers.google.com/style/tense> · CC BY 4.0 · 本文件是**规则摘要**，非原文全文。

## Rule

Use present tense for statements describing general behavior not associated with a particular time.

- Recommended: "Send a query to the service. The server **sends** an acknowledgment."
- Not recommended: "…The server **will send** an acknowledgment."

## Exception: genuinely future actions

Future tense is fine when distinguishing something that happens later in time.

- "Add the filename to the backup list. The file **will be archived** the next time the backup process runs."

## Exception: asynchronous behavior

Future tense suits async operations where the result isn't immediate.

- Recommended: "A message is sent that **will notify** any Pub/Sub subscribers."
- Not recommended: "A message is sent that notifies any Pub/Sub subscribers."

## Restriction

Don't use future tense to describe product behavior expected after a future release. See: future features.

## Avoid hypothetical *would*

- Recommended: "**If** you send an unsubscribe message, the server **removes** you from the mailing list."
- Not recommended: "You can send an unsubscribe message. The server **would then remove** you…"
