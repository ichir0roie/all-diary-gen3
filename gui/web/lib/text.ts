// 画面に出す文言はすべてここに置き、ページ・コンポーネントは文言を直書きしない。
// 日記・コメントの本文は文言ではなく値なので、ここには置かない。

export const T = {
  appName: "All Diary",
  appDescription: "みんなの日記帳",
  loading: "Loading…",
  signInRequired: "Sign in required.",
  crossSiteRejected: "Requests from other sites are not accepted.",
  apiUnreachable: "Cannot reach the API. Try again later.",
  cannotReachApi: (error: string) => `Cannot reach API: ${error}`,

  nav: {
    diary: "Diary",
    tagSearch: "Tag Search",
    past: "Past Day",
    onThisDay: "On This Day",
    heatmap: "Heatmap",
    similar: "Similar",
    data: "Data",
    signOut: "Sign out",
  },

  diary: {
    yearLater: "Year +1",
    yearEarlier: "Year -1",
    weekLater: "Week +1",
    weekEarlier: "Week -1",
    today: "Today",
    now: "Now",
    reference: (time: string) => `At ${time}`,
    boardHint: "Scroll up and down for other days, left and right (Shift + wheel) for other years.",
    day: (day: string, weekday: string) => `${day} ${weekday}`,
    days: (start: string, end: string) => `${start} – ${end}`,
    weekdays: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    span: (year: string, start: string, end: string) => `${year}: ${start} – ${end}`,
    empty: "(no diary)",
    placeholder: "Write today's diary (Ctrl+Enter to post)",
    post: "Post",
    posting: "Posting…",
    menu: "Menu",
    comment: "Comment",
    similar: "Similar diaries",
    edit: "Edit",
    delete: "Delete",
    editTitle: "Edit diary",
    deleteTitle: "Delete diary",
    deleteConfirm: (comments: number) =>
      comments === 0 ? "Delete this diary?" : `Delete this diary and its ${comments} comment${comments === 1 ? "" : "s"}?`,
    save: "Save",
    cancel: "Cancel",
    fromPast: (written: string) => `✉ Sent from ${written}`,
    openWeek: "Open week",
  },

  similar: {
    title: "Similar diaries",
    source: "Diaries similar to this one",
    searchLabel: "Find diaries similar to this text",
    searchPlaceholder: "Type some words or paste a passage",
    hint: "Or click a diary on any page and choose “Similar diaries”.",
    found: (total: number) => `${total} similar diar${total === 1 ? "y" : "ies"}`,
    more: (shown: number, total: number) => `Showing the ${shown} most similar of ${total}.`,
    none: "No similar diary.",
    score: (score: number) => `${Math.round(score * 100)}% match`,
    backToSearch: "Search by text",
  },

  future: {
    open: "Send to future…",
    title: "Send to the future",
    hint: "The diary stays sealed until 0:00 (JST) of the day you pick, then appears on that day.",
    deliverOn: "Deliver on",
    placeholder: "Write to your future self",
    send: "Send",
    sending: "Sending…",
    sent: (day: string) => `Sealed until ${day}.`,
    pending: "On the way",
    pendingItem: (deliver: string, written: string) => `${deliver} (written ${written})`,
    nonePending: "Nothing on the way.",
  },

  dayInput: {
    placeholder: "YYYY/MM/DD",
    calendar: "Calendar",
  },

  past: {
    title: "Write for a past day",
    hint: "Add a diary you did not write on the day. It is placed at the day and time you pick. To write to a future day, use “Send to future…” on the Diary page.",
    day: "Day",
    time: "Time",
    placeholder: "Write the diary of that day (Ctrl+Enter to post)",
    notFuture: "Pick a time before now.",
    posted: (day: string) => `Posted to ${day}.`,
    onDay: (day: string) => `Diaries on ${day}`,
  },

  onThisDay: {
    dayEarlier: "Day -1",
    dayLater: "Day +1",
    today: "Today",
    around: "Range",
    aroundOption: (days: number) => (days === 0 ? "That day" : `±${days} days`),
    heading: (monthDay: string) => `On ${monthDay}`,
    yearsAgo: (year: number, ago: number) => (ago === 0 ? `${year} · this year` : `${year} · ${ago} year${ago === 1 ? "" : "s"} ago`),
    span: (start: string, end: string) => `${start} – ${end}`,
    noDiaryYet: "No diary yet.",
  },

  heatmap: {
    title: "Heatmap",
    metric: "Measure",
    metrics: { diaries: "Diaries", chars: "Characters" },
    yearTotal: (diaries: number, chars: number) => `${diaries.toLocaleString()} diaries · ${chars.toLocaleString()} chars`,
    cell: (day: string, diaries: number, chars: number) => `${day}: ${diaries} diar${diaries === 1 ? "y" : "ies"}, ${chars.toLocaleString()} chars`,
    readoutHint: "Hover a day to see its numbers. Click to open its week.",
    less: "Less",
    more: "More",
    weekdays: ["", "Mon", "", "Wed", "", "Fri", ""],
    months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    noDiaryYet: "No diary yet.",
  },

  tag: {
    menu: "Tag…",
    diaryTitle: "Tag diary",
    commentTitle: "Tag comment",
    search: "Find or create a tag",
    none: "No tag",
    create: (name: string) => `Create “${name}”`,
    noTagYet: "No tag yet. Type a name to create one.",
    save: "Save",
    cancel: "Cancel",

    hint: "A diary or a comment can have one tag. Tag them from the menu of a diary or a comment.",
    newName: "New tag",
    add: "Add",
    name: "Name",
    usage: "Used by",
    usageCount: (diaries: number, comments: number) =>
      `${diaries} diar${diaries === 1 ? "y" : "ies"}, ${comments} comment${comments === 1 ? "" : "s"}`,
    rename: "Rename",
    delete: "Delete",
    deleteTitle: "Delete tag",
    deleteConfirm: (name: string, diaries: number, comments: number) =>
      diaries + comments === 0
        ? `Delete the tag “${name}”?`
        : `Delete the tag “${name}”? It is removed from ${diaries} diar${diaries === 1 ? "y" : "ies"} and ${comments} comment${comments === 1 ? "" : "s"}; the diaries and comments are kept.`,
    deleted: (name: string) => `Deleted “${name}”.`,
  },

  tagSearch: {
    title: "Tag Search",
    hint: "Choose one or more tags. Lists the diaries that have any of them, on the diary itself or on one of its comments. Newest first.",
    noTagYet: "No tag yet. Press Edit to create one.",
    choose: "Choose a tag to list its diaries.",
    clear: "Clear",
    edit: "Edit",
    done: "Done",
    found: (diaries: number) => `${diaries} diar${diaries === 1 ? "y" : "ies"}`,
    none: "No diary has these tags.",
  },

  comment: {
    title: "Comment",
    placeholder: "Write a comment (Ctrl+Enter to save)",
    save: "Save",
    cancel: "Cancel",
    open: "Add comment",
    editTitle: "Edit comment",
    deleteTitle: "Delete comment",
    deleteConfirm: "Delete this comment?",
  },

  data: {
    title: "Data",
    kinds: { diary: "Diary", comment: "Comment" },
    import: "Import",
    importing: "Importing…",
    reading: "Reading…",
    imported: (kind: string, added: number, skipped: number) => `${kind}: added ${added}, skipped ${skipped} already there.`,
    span: (first: string, last: string) => `${first} – ${last}`,

    dbTitle: "Import from the old db file",
    dbHint:
      "Choose the SQLite db file of the old API. Pick whose diaries to import; they become yours. " +
      "Rows already here are skipped, so importing a newer file adds only the new rows.",
    dbFile: "db file",
    noUsers: "No diary in this file.",
    unlinked: (count: number) => `${count} comments point to no diary in this file and cannot be imported.`,
    sourceUser: "User in the file",
    period: "Period",

    csvTitle: "Import from CSV",
    csvHint: "Import the diary CSV first. Comments point to diaries by the diary CSV's id.",
    kind: "Kind",
    csvFile: "CSV file",

    exportTitle: "Export",
    exportHint: "Exported CSV can be imported again (also into another account).",
    export: (kind: string) => `Download ${kind} CSV`,
  },
};
