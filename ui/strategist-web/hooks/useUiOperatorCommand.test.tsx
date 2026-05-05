/** @vitest-environment jsdom */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { type ReactNode, useRef } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as operatorCommandInvalidation from "@/lib/query/operator-command-invalidation";
import { useUiOperatorCommandMutation } from "./useUiOperatorCommand";

const postJson = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/strategist-client", () => ({
  strategistPostJson: (...args: unknown[]) => postJson(...args),
}));

function Harness({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function Caller() {
  const m = useUiOperatorCommandMutation("operator");
  const fired = useRef(false);
  return (
    <button
      type="button"
      onClick={() => {
        if (fired.current) return;
        fired.current = true;
        void m.mutateAsync({
          action: "claim-item",
          mutationToken: "tok",
          request: { operator_id: "op", work_item_key: "w1", idempotency_key: "k" },
        });
      }}
    >
      fire
    </button>
  );
}

describe("useUiOperatorCommandMutation", () => {
  beforeEach(() => {
    cleanup();
    postJson.mockReset();
    postJson.mockResolvedValue({
      status: 200,
      data: { schema_version: "ui_operator_command_receipt/v1", accepted: true, action: "claim-item" },
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("delegates read-plane invalidation to the operator-command invalidation helper", async () => {
    const invSpy = vi
      .spyOn(operatorCommandInvalidation, "invalidateReadPlaneAfterOperatorCommand")
      .mockResolvedValue(undefined);
    const { container } = render(
      <Harness>
        <Caller />
      </Harness>,
    );
    fireEvent.click(within(container).getByRole("button", { name: "fire" }));
    await waitFor(() => expect(postJson).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(invSpy).toHaveBeenCalledTimes(1));
    const receipt = invSpy.mock.calls[0][2];
    expect(receipt).toMatchObject({ accepted: true, action: "claim-item" });
  });

  it("posts only to /ui/commands/{action} facade route", async () => {
    const { container } = render(
      <Harness>
        <Caller />
      </Harness>,
    );
    fireEvent.click(within(container).getByRole("button", { name: "fire" }));
    await waitFor(() => expect(postJson).toHaveBeenCalledTimes(1));
    expect(postJson.mock.calls[0][0]).toBe("/ui/commands/claim-item");
    expect(postJson.mock.calls[0][1]).toMatchObject({ operator_id: "op", work_item_key: "w1" });
    expect(postJson.mock.calls[0][2]).toMatchObject({ mutationToken: "tok", operatorId: "op" });
  });
});
