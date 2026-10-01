import type { KeyboardEvent } from "react";

/** Ctrl+Enter(Mac は ⌘+Enter)。日本語の変換を確定する Enter は除く */
export const isSubmitKey = (e: KeyboardEvent) =>
  e.key === "Enter" && (e.ctrlKey || e.metaKey) && !e.nativeEvent.isComposing;
