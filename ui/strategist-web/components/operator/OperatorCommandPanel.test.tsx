/** @vitest-environment jsdom */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { OperatorCommandPanel } from "./OperatorCommandPanel";

const commandMock = vi.hoisted(() => ({
  mutateAsync: vi.fn(),
}));

vi.mock("@/hooks/useUiOperatorCommand", () => ({
  useUiOperatorCommand: () => ({
    mutateAsync: commandMock.mutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

describe("OperatorCommandPanel", () => {
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

  it("submits a selected workboard target through the governed operator command hook", async () => {
    render(
      <OperatorCommandPanel
        target={{
          work_item_key: "WB-1",
          review_target: "STRAT-1",
          pack_kind: "research-pack",
        }}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /journal claim-item/i }));

    await waitFor(() => expect(commandMock.mutateAsync).toHaveBeenCalledTimes(1));
    expect(commandMock.mutateAsync).toHaveBeenCalledWith({
      action: "claim-item",
      mutationToken: "",
      request: expect.objectContaining({
        operator_id: "operator",
        work_item_key: "WB-1",
        review_target: "STRAT-1",
        pack_kind: "research-pack",
        idempotency_key: expect.stringMatching(/^ui:claim-item:operator:WB-1:/),
      }),
    });
    expect(await screen.findByText("cmd-1")).toBeTruthy();
  });

  it("blocks submission until a governed target identity is selected", () => {
    render(<OperatorCommandPanel target={{ status: "READY" }} />);
    expect((screen.getByRole("button", { name: /journal claim-item/i }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/select a queue row/i)).toBeTruthy();
  });
});
