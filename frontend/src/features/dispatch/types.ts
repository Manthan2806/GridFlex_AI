import type { DispatchData, DispatchUIState } from "../../data/types/domain/dispatch"

export interface DispatchState {
  status: DispatchUIState
  data: DispatchData | null
  error: string | null
  lastFetched: number | null
}

export interface LoadDispatchPayload {
  data: DispatchData
}

export interface SetErrorPayload {
  error: string
}

export interface ResetDispatchPayload {
  [key: string]: never
}