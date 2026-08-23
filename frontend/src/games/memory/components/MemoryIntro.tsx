interface MemoryIntroProps {
  onStart: () => void;
}

export function MemoryIntro({ onStart }: MemoryIntroProps) {
  return (
    <div className="memory-phase memory-intro">
      <h2>Memory Recall Task</h2>
      <p>
        You will see a series of items, one at a time. Try to remember as
        many as you can. Afterwards you'll be asked to recall them a couple
        of times, with a short counting task in between.
      </p>
      <p>There are no right or wrong answers — just do your best.</p>
      <button type="button" onClick={onStart}>
        Start
      </button>
    </div>
  );
}
