/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OperatorCommandPanel } from "./OperatorCommandPanel";

const commandMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
}));

vi.mock("@/hooks/useUiOperatorCommand", () => ({
  useUiOperatorCommandMutation: () => ({
    mutateAsync: commandMock.mutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

describe("OperatorCommandPanel", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    commandMock.mutateAsync.mockReset();
    commandMock.mutateAsync.mockResolvedValue({
      schema_version: "ui_operator_command_receipt/v1",
      accepted: true,
      action: "claim-item",
      status: "ACCEPTED",
      command_id: "cmd-1",
      event_hash: "abc123",
      idempotency_status: "RECORDED",
    });
  });

  const bypassSafety = {
    runtime_mode: "DEV",
    authorization_mode: "NON_PRODUCTION_BYPASS",
    token_configured: false,
    mutation_routes_safe: true,
    detail_code: "REMOTE_NON_PRODUCTION_MUTATION_BYPASS_ENABLED",
  } as const;

  it("submits a selected workboard target through the governed operator command hook", async () => {
    const { container } = render(
      <OperatorCommandPanel
        target={{
          work_item_key: "WB-1",
          review_target: "STRAT-1",
          pack_kind: "research-pack",
        }}
        mutationSafety={bypassSafety}
      />,
    );
    const panel = within(container);

    fireEvent.change(panel.getByTestId("operator-command-operator-id"), { target: { value: "operator" } });
    fireEvent.click(panel.getByTestId("operator-command-submit"));

    await waitFor(() => expect(commandMock.mutateAsync).toHaveBeenCalledTimes(1));
    expect(commandMock.mutateAsync).toHaveBeenCalledWith({
      action: "claim-item",
      mutationToken: undefined,
      tokenDelivery: "authorization_bearer",
      request: expect.objectContaining({
        operator_id: "operator",
        work_item_key: "WB-1",
        review_target: "STRAT-1",
        pack_kind: "research-pack",
        idempotency_key: expect.stringMatching(/^ui:claim-item:operator:WB-1:/),
      }),
    });
    expect(await panel.findByText("cmd-1")).toBeTruthy();
  });

  it("blocks submission until a governed target identity is selected", () => {
    const { container } = render(
      <section aria-label="operator-command-panel-test">
        <OperatorCommandPanel target={{ status: "READY" }} mutationSafety={bypassSafety} />
      </section>,
    );
    const panel = within(container).getByLabelText("operator-command-panel-test");
    fireEvent.change(within(panel).getByTestId("operator-command-operator-id"), { target: { value: "ops" } });
    expect((within(panel).getByTestId("operator-command-submit") as HTMLButtonElement).disabled).toBe(true);
    expect(within(panel).getByText(/select a queue row/i)).toBeTruthy();
  });

  it("disables submit without operator id even when target is present", () => {
    const { container } = render(
      <OperatorCommandPanel target={{ work_item_key: "WB-9" }} mutationSafety={bypassSafety} />,
    );
    const panel = within(container);
    expect((panel.getByTestId("operator-command-submit") as HTMLButtonElement).disabled).toBe(true);
    expect(panel.getByTestId("operator-command-disabled-reasons").textContent).toContain("OPERATOR_ID_REQUIRED");
  });

  it("requires token when backend is TOKEN_PROTECTED", () => {
    const { container } = render(
      <OperatorCommandPanel
        target={{ work_item_key: "WB-1" }}
        mutationSafety={{
          runtime_mode: "PRODUCTION",
          authorization_mode: "TOKEN_PROTECTED",
          token_configured: true,
          mutation_routes_safe: true,
          detail_code: "MUTATION_TOKEN_CONFIGURED",
        }}
      />,
    );
    const panel = within(container);
    fireEvent.change(panel.getByTestId("operator-command-operator-id"), { target: { value: "ops" } });
    expect(panel.getByTestId("operator-command-disabled-reasons").textContent).toContain("MUTATION_TOKEN_REQUIRED");
    expect((panel.getByTestId("operator-command-submit") as HTMLButtonElement).disabled).toBe(true);
  });

  it("does not persist token to localStorage when typing", () => {
    const spy = vi.spyOn(Storage.prototype, "setItem");
    const { container } = render(<OperatorCommandPanel target={{ work_item_key: "x" }} mutationSafety={bypassSafety} />);
    const panel = within(container);
    fireEvent.change(panel.getByTestId("operator-command-mutation-token"), { target: { value: "secret" } });
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
});
