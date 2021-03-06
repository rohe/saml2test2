<%!
    def link(url):
        return "<a href='%sreset'>link</a>" % url

    def prnt(a_string):
        return a_string
%>

<!DOCTYPE html>

<html>
  <head>
    <title>SAML2 IdP Test</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Bootstrap -->
    <link href="static/bootstrap/css/bootstrap.min.css" rel="stylesheet" media="screen">
      <link href="static/style.css" rel="stylesheet" media="all">

    <!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
      <script src="../../assets/js/html5shiv.js"></script>
      <script src="../../assets/js/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <div class="container">
     <!-- Main component for a primary marketing message or call to action -->
      <div class="jumbotron">
        <h4>SAML2 IdP Test</h4>
        <p>Sorry, an error occured. To restart click this ${link(htmlpage)}.</p>
        <p>Error message: ${prnt(error_msg)}</p>
        <p>${prnt(context_msg)}</p>
        <hr>
        <p style="font-family: monospace; overflow-x: auto; font-size:0.8em;">${prnt(traceback_msg)}</p>
      </div>

    </div> <!-- /container -->
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="/static/jquery.min.1.9.1.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="/static/bootstrap/js/bootstrap.min.js"></script>

  </body>
</html>
