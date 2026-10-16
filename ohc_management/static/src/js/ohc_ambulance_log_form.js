/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

class OhcAmbulanceLogFormController extends FormController {
    async _confirmBeforeLeaving() {
        // await this.model.root.askChanges();
        // if (!this.model.root.isDirty) {
        //     return true;
        // }
        if (typeof this.model.root.askChanges === "function") {
                await this.model.root.askChanges();
            }
            if (!this.model.root.isDirty) {
                return true;
            }
        return new Promise((resolve) => {
            this.dialogService.add(ConfirmationDialog, {
                title: this.env._t("Unsaved changes"),
                body: this.env._t(
                    "You have unsaved changes on this log (e.g. Vehicle changed). You must discard these changes before continuing."
                ),
                confirmLabel: this.env._t("Discard changes"),
                confirm: async () => {
                    await this.model.root.discard();
                    resolve(true);
                },
            });
        });
    }

    async onPagerUpdate({ offset, resIds }) {
        const canProceed = await this._confirmBeforeLeaving();
        if (canProceed) {
            return this.model.load({ resId: resIds[offset] });
        }
    }

    async beforeLeave() {
        return this._confirmBeforeLeaving();
    }

    async create() {
        const canProceed = await this._confirmBeforeLeaving();
        if (canProceed) {
            this.disableButtons();
            await this.model.load({ resId: null });
            this.enableButtons();
        }
    }
}

registry.category("views").add("ohc_ambulance_log_no_autosave_form", {
    ...formView,
    Controller: OhcAmbulanceLogFormController,
});