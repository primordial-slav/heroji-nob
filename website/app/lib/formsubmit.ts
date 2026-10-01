// FormSubmit answers 200 even when it did not deliver the message (e.g. "This form needs Activation"),
// with {"success": "false", "message": ...} in the body; only "success": "true" means it was sent.
export async function wasDelivered(res: Response): Promise<boolean> {
  if (!res.ok) return false
  try {
    const data = await res.json()
    return data?.success === true || data?.success === 'true'
  } catch {
    return false
  }
}
