<%!
    page_title_ = '修改过期密码'
%>
<%inherit file="../page_single_base.mako"/>

<%block name="extend_js_file">
    <script type="text/javascript" src="${ static_url('js/user/change-expired-password.js') }"></script>
</%block>

<%block name="embed_css">
    <style type="text/css">
        .input-addon-desc {
            text-align: right;
            font-size: 90%;
            color: #707070;
        }

        .captcha-box {
            padding: 0 5px;
        }
    </style>
</%block>

<%block name="page_header">
    <div class="container-fluid top-navbar">
        <div class="brand"><a href="/"><span class="site-logo"></span></a></div>
        <div class="breadcrumb-container">
            <ol class="breadcrumb">
                <li><i class="fa fa-key"></i> 修改过期密码</li>
            </ol>
        </div>
    </div>
##     <a href="http://tp4a.com/" target="_blank"><span class="logo"></span></a>
</%block>

<div class="page-content">
    <div class="info-box">
        <div class="info-icon-box">
            <i class="fa fa-key" style="color:#ffa043;"></i>
        </div>
        <div class="info-message-box">
            <div id="title" class="title">密码已过期</div>
            <hr/>
            <div id="content" class="content">

                <div id="area-input">
                    <div class="row">
                        <div class="col-md-5">
                            <div class="input-group">
                                <span class="input-group-addon"><i class="fa fa-user fa-fw"></i></span>
                                <input id="txt-username" type="text" class="form-control mono" disabled>
                            </div>

                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="fa fa-key fa-fw"></i></span>
                                <input id="txt-password" type="password" class="form-control mono" placeholder="输入当前密码" data-toggle="popover" data-trigger="manual" data-placement="top">
                            </div>

                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="fa fa-edit fa-fw"></i></span>
                                <input id="txt-new-password" type="password" class="form-control mono" placeholder="设置新密码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-btn"><button class="btn btn-default" type="button" id="btn-switch-password"><i id="icon-switch-password" class="fa fa-eye fa-fw"></i></button></span>
                            </div>

                            <div class="input-group" style="margin-top:10px;">
                                <span class="input-group-addon"><i class="far fa-check-square fa-fw"></i></span>
                                <input id="txt-captcha" type="text" class="form-control" placeholder="验证码" data-toggle="popover" data-trigger="manual" data-placement="top">
                                <span class="input-group-addon captcha-box"><a href="javascript:;" tabindex="-1"><img id="img-captcha" src=""></a></span>
                            </div>
                            <p class="input-addon-desc">验证码，点击图片可更换</p>

                            <div style="margin:20px 0;">
                                <button type="button" class="btn btn-primary" id="btn-submit" style="width:100%;"><i class="fa fa-check fa-fw"></i> 确定修改</button>
                                <div id="message" style="display: none;"></div>
                            </div>

                        </div>
                        <div class="col-md-7">
                            <div class="alert alert-danger">
                                <p>您的登陆密码已过期，根据系统设置，在您修改密码之前，将无法登陆CLOUDFORT系统。</p>
                            </div>
                            <div id="info" class="alert alert-warning" style="display:none;">
                                <p>注意，系统启用强密码策略，要求密码至少8位，必须包含大写字母、小写字母以及数字。</p>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</div>

<%block name="embed_js">
    <script type="text/javascript">
        "use strict";
        $app.add_options(${page_param});
        console.log($app.options);
    </script>
</%block>
