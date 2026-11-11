/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";


/**
 * ============================================================
 * LIST VIEW
 * ============================================================
 */
patch(ListController.prototype, "ohc_management_delete_visibility_list", {

    setup() {
        this._super.apply(this, arguments);

        this.userService = useService("user");

        this.canShowDelete = false;

        onWillStart(async () => {
            const hasAllowDelete = await this.userService.hasGroup(
                "ohc_management.group_allow_delete_option"
            );

            const isSystemAdmin = this.userService.isSystem;
            const isOHCManagement = this.props.resModel === "ohc.management";

            this.canShowDelete =
                hasAllowDelete &&
                (!isOHCManagement || isSystemAdmin);
        });
    },

    getActionMenuItems() {
        const actionMenus = this._super.apply(this, arguments);

        if (!this.canShowDelete && actionMenus.other) {
            actionMenus.other = actionMenus.other.filter(
                (item) => item.key !== "delete"
            );
        }

        return actionMenus;
    },
});


/**
 * ============================================================
 * FORM VIEW
 * ============================================================
 */
patch(FormController.prototype, "ohc_management_delete_visibility_form", {

    setup() {
        this._super.apply(this, arguments);

        this.userService = useService("user");

        this.canShowDelete = false;

        onWillStart(async () => {
            const hasAllowDelete = await this.userService.hasGroup(
                "ohc_management.group_allow_delete_option"
            );

            const isSystemAdmin = this.userService.isSystem;
            const isOHCManagement = this.props.resModel === "ohc.management";

            this.canShowDelete =
                hasAllowDelete &&
                (!isOHCManagement || isSystemAdmin);
        });
    },

    getActionMenuItems() {
        const actionMenus = this._super.apply(this, arguments);

        if (!this.canShowDelete && actionMenus.other) {
            actionMenus.other = actionMenus.other.filter(
                (item) => item.key !== "delete"
            );
        }

        return actionMenus;
    },
});