"use strict";

$app.on_init = function (cb_stack) {
    $app.dom = {
        title: $('#title'),
        icon_bg: $('#icon-bg'),

        op_message: $('#message'),

        error: {
            area: $('#area-error'),
            message: $('#area-error [data-field="message"]')
        },

        txt_username: $('#txt-username'),
        txt_password: $('#txt-password'),
        txt_new_password: $('#txt-new-password'),
        btn_switch_password: $('#btn-switch-password'),
        icon_switch_password: $('#icon-switch-password'),
        txt_captcha: $('#txt-captcha'),
        img_captcha: $('#img-captcha'),
        btn_submit: $('#btn-submit'),

        info: $('#info'),

        find: {
            area: $('#area-find-password'),
            input_email: $('#area-find-password [data-field="input-email"]'),
            input_captcha: $('#area-find-password [data-field="input-captcha"]'),
            btn_submit: $('#area-find-password [data-field="btn-submit"]'),
            message: $('#area-find-password [data-field="message"]')
        },

        set_password: {
            area: $('#area-set-password'),
            info: $('#area-set-password [data-field="info"]'),
            input_password: $('#area-set-password [data-field="input-password"]'),
            btn_switch_password: $('#area-set-password [data-field="btn-switch-password"]'),
            btn_switch_password_icon: $('#area-set-password [data-field="btn-switch-password"] i'),
            message: $('#area-set-password [data-field="message"]')
        }
    };

    $app.dom.img_captcha.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
    $app.dom.txt_password.focus();
    $app.dom.txt_username.val($app.options.username);
    if ($app.options.force_strong)
        $app.dom.info.show();

    $app.dom.img_captcha.click(function () {
        $(this).attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
        $app.dom.txt_captcha.focus().val('');
    });

    $app.dom.btn_submit.click(function () {
        $app.on_change_password();
    });

    $app.dom.txt_password.keydown(function (event) {
        if (event.which === 13) {
            $app.dom.txt_new_password.focus();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });
    $app.dom.txt_new_password.keydown(function (event) {
        if (event.which === 13) {
            $app.dom.txt_captcha.focus();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });
    $app.dom.txt_captcha.keydown(function (event) {
        if (event.which === 13) {
            $app.on_change_password();
        } else {
            $app.hide_op_box();
            $('[data-toggle="popover"]').popover('hide');
        }
    });

    $app.dom.btn_switch_password.click(function () {
        if ('password' === $app.dom.txt_new_password.attr('type')) {
            $app.dom.txt_new_password.attr('type', 'text');
            $app.dom.icon_switch_password.removeClass('fa-eye').addClass('fa-eye-slash')
        } else {
            $app.dom.txt_new_password.attr('type', 'password');
            $app.dom.icon_switch_password.removeClass('fa-eye-slash').addClass('fa-eye')
        }
    });

    cb_stack.exec();
};

$app.hide_op_box = function () {
    $app.dom.op_message.hide();
};

$app.show_op_box = function (op_type, op_msg) {
    $app.dom.op_message.html(op_msg);
    $app.dom.op_message.removeClass().addClass('op_box op_' + op_type);
    $app.dom.op_message.show();
};

// $app.on_send_find_password_email = function () {
//     $app.hide_op_box();
//     var str_username = $app.dom.find.input_username.val();
//     var str_email = $app.dom.find.input_email.val();
//     var str_captcha = $app.dom.find.input_captcha.val();
//
//     if (str_username.length === 0) {
//         $app.show_op_box('error', '?????????????????????');
//         $app.dom.find.input_username.attr('data-content', "???????????????????????????").focus().popover('show');
//         return;
//     }
//
//     if (str_email.length === 0) {
//         $app.show_op_box('error', '??????????????????????????????');
//         $app.dom.find.input_email.attr('data-content', "????????????????????????????????????").focus().popover('show');
//         return;
//     }
//
//     if (!tp_is_email(str_email)) {
//         $app.show_op_box('error', '??????????????????????????????');
//         $app.dom.find.input_email.attr('data-content', "???????????????????????????????????????").focus().popover('show');
//         return;
//     }
//
//     if (str_captcha.length !== 4) {
//         $app.show_op_box('error', '??????????????????');
//         $app.dom.find.input_captcha.attr('data-content', "????????????4????????????????????????????????????????????????").focus().select().popover('show');
//         return;
//     }
//
//     $app.dom.find.btn_submit.attr('disabled', 'disabled');
//     $tp.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 // ????????????
//                 $app.hide_op_box();
//                 $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> ?????????????????????????????????????????????...');
//                 $app.do_send_reset_email(str_username, str_email, str_captcha);
//             }
//             else {
//                 $app.dom.find.btn_submit.removeAttr('disabled');
//                 $app.hide_op_box();
//                 $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
//                 $app.dom.captcha_image.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
//                 $app.dom.input_captcha.focus().select().val('');
//             }
//         },
//         function () {
//             $app.hide_op_box();
//             $app.show_op_box('error', '????????????????????????????????????????????????????????????');
//             $app.dom.find.btn_submit.removeAttr('disabled');
//         }
//     );
// };
//
// $app.do_send_reset_email = function (str_username, str_email, str_captcha) {
//     $tp.ajax_post_json('/user/do-reset-password', {
//             mode: 3,
//             username: str_username,
//             email: str_email,
//             captcha: str_captcha
//         },
//         function (ret) {
//             if (ret.code === TPE_OK) {
//                 $app.dom.find.btn_submit.slideUp('fast');
//                 $app.show_op_box('success', '???????????????????????????????????????????????????');
//             } else {
//                 $app.dom.find.btn_submit.removeAttr('disabled');
//                 $app.hide_op_box();
//                 var msg = '';
//                 if (ret.code === TPE_NOT_EXISTS)
//                     msg = tp_error_msg(ret.code, '??????????????????????????????????????????????????????????????????????????????');
//                 else
//                     msg = tp_error_msg(ret.code, ret.message);
//                 $app.show_op_box('error', msg);
//             }
//         },
//         function () {
//             $app.dom.find.btn_submit.removeAttr('disabled');
//             $app.hide_op_box();
//             $app.show_op_box('error', '???????????????????????????????????????????????????');
//         },
//         15000
//     );
// };

$app.on_change_password = function () {
    $app.hide_op_box();
    var str_password = $app.dom.txt_password.val();
    var str_new_password = $app.dom.txt_new_password.val();
    var str_captcha = $app.dom.txt_captcha.val();

    if (str_password.length === 0) {
        $app.show_op_box('error', '??????????????????');
        $app.dom.txt_password.attr('data-content', "??????????????????????????????").focus().popover('show');
        return;
    }
    if (str_new_password.length === 0) {
        $app.show_op_box('error', '????????????????????????');
        $app.dom.txt_new_password.attr('data-content', "???????????????????????????").focus().popover('show');
        return;
    }

    if (str_captcha.length !== 4) {
        $app.show_op_box('error', '??????????????????');
        $app.dom.txt_captcha.attr('data-content', "????????????4????????????????????????????????????????????????").focus().select().popover('show');
        return;
    }

    if ($app.options.force_strong) {
        if (!tp_check_strong_password(str_new_password)) {
            $app.show_op_box('error', tp_error_msg(TPE_FAILED, '?????????????????????????????????'));
            $app.dom.txt_new_password.attr('data-content', "???????????????????????????8????????????????????????????????????????????????????????????").focus().popover('show');
            return;
        }
    }

    $app.dom.btn_submit.attr('disabled', 'disabled');
    $tp.ajax_post_json('/auth/verify-captcha', {captcha: str_captcha},
        function (ret) {
            if (ret.code === TPE_OK) {
                // ????????????
                $app.hide_op_box();
                $app.show_op_box('wait', '<i class="fa fa-circle-o-notch fa-spin"></i> ??????????????????????????????...');
                $app.do_change_password(str_password, str_new_password, str_captcha);
            }
            else {
                $app.dom.btn_submit.removeAttr('disabled');
                $app.hide_op_box();
                $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
                $app.dom.img_captcha.attr('src', '/auth/captcha?h=28&rnd=' + Math.random());
                $app.dom.txt_captcha.focus().select().val('');
            }
        },
        function () {
            $app.hide_op_box();
            $app.show_op_box('error', '????????????????????????????????????????????????????????????');
            $app.dom.btn_submit.removeAttr('disabled');
        }
    );
};

$app.do_change_password = function (str_password, str_new_password, str_captcha) {
    // var str_username = $app.options.username;
    $tp.ajax_post_json('/user/do-reset-password', {
            mode: 6,
            username: $app.options.username,
            password: str_password,
            new_password: str_new_password,
            captcha: str_captcha
        },
        function (ret) {
            $app.dom.btn_submit.removeAttr('disabled');
            if (ret.code === TPE_OK) {
                $app.show_op_box('success', '?????????????????????????????????????????????');
                setTimeout(function () {
                    window.location.href = '/';
                }, 2000);
            } else {
                $app.show_op_box('error', tp_error_msg(ret.code, ret.message));
            }
        },
        function () {
            $app.dom.find.btn_submit.removeAttr('disabled');
            $app.hide_op_box();
            $app.show_op_box('error', '????????????????????????????????????');
        }
    );
};
