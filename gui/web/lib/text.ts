// 画面に出す文言はすべてここに置き、ページ・コンポーネントは文言を直書きしない。
// 日記・コメントの本文は文言ではなく値なので、ここには置かない。

export const T = {
  appName: "all diary",
  appDescription: "Diary with comments, three years side by side",
  loading: "Loading…",
  signInRequired: "Sign in required.",
  cannotReachApi: (error: string) => `Cannot reach API: ${error}`,

  nav: {
    diary: "Diary",
    data: "Data",
    signOut: "Sign out",
  },

  diary: {
    yearLater: "Year +1",
    yearEarlier: "Year -1",
    weekLater: "Week +1",
    weekEarlier: "Week -1",
    today: "Today",
    span: (year: string, start: string, end: string) => `${year}: ${start} – ${end}`,
    empty: "(no diary)",
    placeholder: "Write today's diary",
    post: "Post",
    posting: "Posting…",
  },

  comment: {
    title: "Comment",
    placeholder: "Write a comment",
    save: "Save",
    cancel: "Cancel",
    open: "Add comment",
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
