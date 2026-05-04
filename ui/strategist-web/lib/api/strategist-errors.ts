export type StrategistApiErrorKind = "generic" | "unauthorized" | "unavailable";

export class StrategistApiError extends Error {
  override readonly name = "StrategistApiError";
  constructor(
    message: string,
    readonly httpStatus?: number,
    readonly detail?: string,
    readonly kind: StrategistApiErrorKind = "generic",
  ) {
    super(message);
  }
}
