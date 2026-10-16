/** @odoo-module **/

import { useState } from "@odoo/owl";
import { ImportRecords, importRecordsItem } from "@base_import/import_records/import_records";
import { useService } from "@web/core/utils/hooks";


export class OHCImportRecords extends ImportRecords {

    setup() {
        super.setup();

        this.user = useService("user");

        this.state = useState({
            canImport: false,
        });

        this._checkImportPermission();
    }

    async _checkImportPermission() {
        const hasImportGroup = await this.user.hasGroup(
            "ohc_management.group_allow_import"
        );

        const isSystemAdmin = this.user.isSystem;

        const resModel = this.env.searchModel.resModel;

        /*
         * Rules:
         *
         * 1. Without Allow Import group:
         *    → Import hidden everywhere
         *
         * 2. Allow Import + normal user:
         *    → Import available everywhere EXCEPT OHC Management
         *
         * 3. Allow Import + System Administrator:
         *    → Import available everywhere including OHC Management
         */

        if (!hasImportGroup) {
            this.state.canImport = false;
            return;
        }

        if (resModel === "ohc.management" && !isSystemAdmin) {
            this.state.canImport = false;
            return;
        }

        this.state.canImport = true;
    }
}

OHCImportRecords.template = "ohc_management.ImportRecords";


// Replace the original ImportRecords component
importRecordsItem.Component = OHCImportRecords;