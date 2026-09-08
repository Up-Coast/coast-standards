import { Component, Input } from '@angular/core';

/** The panel's view. */
@Component({
  selector: 'status-panel',
  template: `<section>{{ title }}</section>`,
})
export class StatusPanel {
  /** The heading. */
  @Input() title = '';
  /** Writes the panel to disk. */
  save() {}
  private cache() {}
}

/** Greets by name. */
export function greet(name: string) {
  return "Hello, " + name;
}

/** Sits directly above its declaration. */
export function attached() {}

/** A comment line between the doc and the declaration is transparent. */
// eslint-disable-next-line no-empty-function
export function afterComment() {}

/** A double quote inside a single-quoted string. */
export const quote = 'He said "hi"';

/** A double quote and an interpolation inside a template string. */
export const banner = `Say "hello" to ${greet("you")}`;

/** An apostrophe in JSX text opens no string. */
export function Note() {
  return <p>Don't panic</p>;
}

/** Still seen after the strings above. */
export function afterStrings() {}
