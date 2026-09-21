One lamp count in the top bar. The needs-you counter is a button that jumps to the next orange ticket; the others are plain.

```jsx
<Counter button hot lamp="orange" label="needs you" count={3} onClick={jump} />
<Counter lamp="green" label="running" count={3} sub="waiting for a slot 1" />
```

It renders the product's own markup and classes; pass the product's view data as is.
