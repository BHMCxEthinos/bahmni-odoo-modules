/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class StockPickingListController extends ListController {

    setup() {
        super.setup();
        this.actionService = useService("action");
        this.orm = useService("orm");
    }

    // onClickScrap() {
    //     const selectedIds = this.model.root.selection.map((record) => record.resId);

    //     const context = {};
    //     if (selectedIds.length === 1) {
    //         context.default_picking_id = selectedIds[0];
    //     }

    //     this.actionService.doAction({
    //         type: "ir.actions.act_window",
    //         name: "Scrap",
    //         res_model: "stock.scrap",
    //         views: [[false, "form"]],
    //         target: "current",
    //         context: context,
    //     });
    // }

    async onClickScrap() {
    const selectedIds = this.model.root.selection.map((record) => record.resId);
    const rootLocationId = this.props.context.ohc_root_location_id;

    const context = {
        ohc_root_location_id: rootLocationId,
    };

    if (selectedIds.length === 1) {
        context.default_picking_id = selectedIds[0];
    }

    if (rootLocationId) {
        const clinicLocationId = await this._getClinicLocationId(rootLocationId);
        if (clinicLocationId) {
            context.default_location_id = clinicLocationId;
        }
    }

    this.actionService.doAction({
        type: "ir.actions.act_window",
        name: "Scrap",
        res_model: "stock.scrap",
        views: [[false, "form"]],
        target: "current",
        context: context,
    });
}

async _getClinicLocationId(rootLocationId) {
    const locations = await this.orm.searchRead(
        "stock.location",
        [
            ["id", "child_of", rootLocationId],
            ["name", "=", "Clinic"],
        ],
        ["id"]
    );
    return locations.length ? locations[0].id : null;
}
}

export const StockPickingListView = {
    ...listView,
    Controller: StockPickingListController,
    buttonTemplate: "ohc_management.StockPickingListView.Buttons",
};

registry.category("views").add("ohc_stock_picking_list", StockPickingListView);