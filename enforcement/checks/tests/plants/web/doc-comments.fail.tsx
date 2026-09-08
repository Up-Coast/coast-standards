import { Component, Input } from '@angular/core';

/** The panel's view. */
@Component({
  selector: 'status-panel',
  template: `<section>{{ title }}</section>`,
})
export class StatusPanel {
  @Input() title = '';
  save() {}
}

export function greet(name: string) {
  return "Hello, " + name;
}

/** Documented, but a blank line sits between this and the declaration. */

export function orphaned() {}

export const quote = 'He said "hi"';

export const banner = `Say "hello" to ${greet("you")}`;

export function Note() {
  return <p>Don't panic</p>;
}

export function afterStrings() {}
