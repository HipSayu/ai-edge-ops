export default function ErrorText({ message }: { message: string | null }) {
  return message ? <p className="rounded-lg bg-danger/10 px-3 py-2 text-sm text-danger">{message}</p> : null
}
