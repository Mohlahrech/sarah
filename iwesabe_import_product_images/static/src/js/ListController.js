odoo.define('iwesabe_import_product_images.import_product_image_button', function (require) {
    "use strict";
    
    var core = require('web.core');
	var ListController = require('web.ListController');
	var _t = core._t;

    ListController.include({
		renderButtons: function ($node) {
			this._super.apply(this, arguments);
            if (this.$buttons){
				this.$buttons.find('.o_open_varient_import_imag').click(this.proxy('action_varient_import_images'));
                this.$buttons.find('.o_open_template_import_imag').click(this.proxy('action_template_import_images'));
			}
		},
		action_varient_import_images:function(){
			this.do_action({
				name: _t('Import Images'),
				type: 'ir.actions.act_window',
				res_model: 'product.import.image',
				views: [[false, 'form']],
				view_mode: 'form',
				target: 'new',
                context:{'model_name':'product.product'}
			});
		},
        action_template_import_images:function(){
			this.do_action({
				name: _t('Import Images'),
				type: 'ir.actions.act_window',
				res_model: 'product.import.image',
				views: [[false, 'form']],
				view_mode: 'form',
				target: 'new',
                context:{'model_name':'product.template'}
			});
		}
	})

});