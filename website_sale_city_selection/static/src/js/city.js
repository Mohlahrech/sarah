odoo.define('website_custom_address',['website_sale.website_sale'], function (require,d) {
    'use strict';
    
    var website_sale= require('website_sale.website_sale')

    website_sale.WebsiteSale.include({
        events: _.extend({}, website_sale.WebsiteSale.prototype.events || {}, {
            'change select[name="state_id"]': '_onChangeState',
            'change select[name="city_id"]': '_onChangeCity',
        }),

        /**
         * @private
         * @param {Event} ev
         */
        _onChangeState: function (ev) {
            if (!this.$('.checkout_autoformat').length) {
                return;
            }
            this._changeState();
        },

        /**
         * @private
         */
        _changeCountry: function () {
            if (!$("#country_id").val()) {
                $("select[name='state_id']").parent('div').hide();

                return;
            }
            var selectStates = $("select[name='state_id']");
            if (selectStates.data('init') === 0) {
                $("#state_id").children("option:selected").prop("selected", false)
                $("input[name='city']").val('')
            }
            this._rpc({
                route: "/shop/country_infos/" + $("#country_id").val(),
                params: {
                    mode: 'shipping',
                },
            }).then(function (data) {
                // populate states and display
                $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');
                var selectCities = $("select[name='city_id']");
                var required_fields = $("input[name='field_required']").val().split(',')
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init') === 0 || selectStates.find('option').length === 1) {
                    if (data.states.length) {
                        $("input[name='city']").parent('div').css({ "display": "none" })

                        if (required_fields.indexOf("city_id") !== -1) {
                            $("input[name='field_required']").val('phone,name,city_id,state_id')
                        }
                        else {
                            $("input[name='field_required']").val('phone,name,state_id')
                        }
                        selectStates.html('');
                        selectStates.append($('<option>').text('State / Province...').attr('value', ''));

                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    }
                    else {
                        $("input[name='city']").parent('div').css({ "display": "" })
                        selectStates.val('').parent('div').hide();
                        selectCities.val('').parent('div').hide();

                        if (required_fields.indexOf("city_id") !== -1) {
                            $("input[name='field_required']").val('phone,name,city_id')
                        } else {
                            $("input[name='field_required']").val('phone,name')
                        }

                        $("#state_id").children("option:selected").prop("selected", false)
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }

                // manage fields order / visibility
                if (data.fields) {
                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)) {
                        $(".div_zip").before($(".div_city"));
                    } else {
                        $(".div_zip").after($(".div_city"));
                    }
                    var all_fields = ["street", "zip", "country_name"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields) >= 0);
                    });
                }
            });
        },

        /**
         * @private
         */
        _changeState: function () {
            if (!$("#state_id").val()) {
                $("select[name='city_id']").parent('div').hide();
                $("input[name='city']").val('')
                $("select[name='city_id']").val('')
                return;
            }
            var selectCities = $("select[name='city_id']");

            $("input[name='city']").val('')
            $("select[name='city_id']").val('')
            this._rpc({
                route: "/shop/state_infos/" + $("#state_id").val(),
                params: {
                    mode: 'shipping',
                },
            }).then(function (data) {
                // populate states and display
                var required_fields = $("input[name='field_required']").val().split(',')

                // dont reload state at first loading (done in qweb)
                if (selectCities.data('init') === 0 || selectCities.find('option').length === 1) {
                    if (data.cities.length) {
                        $("input[name='city']").parent('div').css({ "display": "none" })
                        selectCities.html('');
                        if (required_fields.indexOf("state_id") !== -1) {
                            $("input[name='field_required']").val('phone,name,state_id,city_id')
                        }
                        else {
                            $("input[name='field_required']").val('phone,name,city_id')
                        }
                        selectCities.append($('<option>').text('City...').attr('value', ''));
                        _.each(data.cities, function (x) {
                            var opt = $('<option>').text(x[1]).attr('value', x[0]);
                            selectCities.append(opt);
                        });
                        selectCities.parent('div').show();
                    }
                    else {
                        selectCities.val('').parent('div').hide();
                        if (required_fields.indexOf("state_id") !== -1) {
                            $("input[name='field_required']").val('phone,name,state_id')
                        } else {
                            $("input[name='field_required']").val('phone,name')
                        }
                        $("input[name='city']").parent('div').css({ "display": "" })
                    }
                    selectCities.data('init', 0);
                }
                else {
                    selectCities.data('init', 0);
                }
            });
        },

        _onChangeCity: function () {
            var selected_city = $("#city_id").children("option:selected").val()
            if (selected_city) {
                $("input[name='city']").val($("#city_id").children("option:selected").text().trim())
            }
            else {
                $("input[name='city']").val('')
            }
        },
    });
});