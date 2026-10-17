"use client";

import { useRef, useState } from "react";
import { parseDayText, slashDay } from "@/lib/date";
import { T } from "@/lib/text";

type Props = {
  id?: string;
  // "YYYY-MM-DD"。打ちかけで読めないあいだは ""
  value: string;
  min?: string;
  max?: string;
  disabled?: boolean;
  onChange: (day: string) => void;
};

/** 日付の欄。"YYYY/MM/DD" の文字で打つ。<input type="date"> の見た目はブラウザの言語で決まり(英語なら mm/dd/yyyy)、ページから変えられないため。
 * カレンダーからも選べるよう、隠した <input type="date"> の選び窓をボタンで開く */
export default function DayInput({ id, value, min, max, disabled, onChange }: Props) {
  const [text, setText] = useState(slashDay(value));
  const [shownValue, setShownValue] = useState(value);
  const picker = useRef<HTMLInputElement>(null);

  // カレンダーで選んだときなど、外から値が変わったら欄の文字をそろえる(打ちかけの文字が同じ日を指していれば、そのままにする)
  if (value !== shownValue) {
    setShownValue(value);
    if (parseDayText(text) !== value) setText(slashDay(value));
  }

  const day = parseDayText(text);
  const invalid = text.trim() !== "" && (day === "" || (min !== undefined && day < min) || (max !== undefined && day > max));

  return (
    <span className="day-input">
      <input
        id={id}
        type="text"
        inputMode="numeric"
        placeholder={T.dayInput.placeholder}
        value={text}
        disabled={disabled}
        aria-invalid={invalid}
        onChange={(e) => {
          setText(e.target.value);
          onChange(parseDayText(e.target.value));
        }}
        // 区切り無しの 8 桁などで打っても、離れたら "YYYY/MM/DD" に整える
        onBlur={() => day && setText(slashDay(day))}
      />
      <button type="button" disabled={disabled} onClick={() => picker.current?.showPicker()}>
        {T.dayInput.calendar}
      </button>
      <input
        ref={picker}
        type="date"
        className="picker"
        tabIndex={-1}
        aria-hidden
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </span>
  );
}
