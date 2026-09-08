import React, {
  Button,
  Card as Panel,
} from "./ui";
import type {
  Entry,
} from "./types";
export {
  Panel,
};
type Of<T extends Entry["type"]> = Extract<Entry, { type: T }>;
const act = (fn: () => Promise<unknown>) => () => run(fn);
const writeRow = async (fields: Record<string, unknown>): Promise<string> => save(fields);
enum State {
  Active,
  Inactive
}
export const Home = ({ a, b, max, now, startMs, endMs, parts }) => {
  if (a > 0 && b < max) return null;
  return (
    <Panel>
      {now >= startMs && now <= endMs ? parts.map((part, i) => (i % 2 === 1 ? <strong key={i}>{part}</strong> : part)) : null}
      <Button>{t('home.saveButton')}</Button>
      <p>
        {t('home.explanation')}
      </p>
    </Panel>
  );
};
