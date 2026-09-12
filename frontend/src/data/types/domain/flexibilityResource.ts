export type ResourceState = "available" | "dispatched" | "completed" | "unavailable"

export interface FlexibilityResource {
  readonly id: string
  readonly type: string
  readonly location_id: string
  readonly rated_power_kw: number
  readonly earliest_start: string
  readonly latest_end: string
  readonly required_kwh: number
  readonly minimum_kwh: number
  readonly maximum_kwh: number
  readonly minimum_duration: number
  readonly maximum_duration: number
  readonly deadline: string
  readonly min_power: number
  readonly max_power: number
  readonly historical_response: number
  readonly override_rate: number
  readonly availability_rate: number
  readonly potential_kw: number
  readonly expected_kw: number
  readonly trusted_kw: number
  readonly confidence: number
  readonly state: ResourceState
}
