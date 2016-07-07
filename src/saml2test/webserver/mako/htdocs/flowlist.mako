<%!

def op_choice(base, nodes, test_info, headlines, tc_id_infobase):
    """
    Creates a list of test flows
    """
    _grp = "_"
    color = ['<img src="site/static/black.png" alt="Black" height="50%">',
             '<img src="site/static/green.png" alt="Green" height="50%">',
             '<img src="site/static/yellow.png" alt="Yellow" height="50%">',
             '<img src="site/static/red.png" alt="Red" height="50%">',
             '<img src="site/static/qmark.jpg" alt="QuestionMark" height="50%">',
             '<img src="site/static/greybutton" alt="Grey" height="50%">',
             ]
    element = ['<ul style="list-style-type: none;">']

    for node in nodes:
        p, grp, spec = node.name.split("-", 2)
        if not grp == _grp:
            _grp = grp
            element.append("<hr size=2><h3 id='%s'>%s</h3>" % (_grp, headlines[_grp]))
        node_link = "_" + node.tc_id.replace("-","_")
        element.append("<li><a href='%s%s'>%s</a>%s (%s) [<a href='%s%s' target='_blank'>%s<a>] " % (base,
            node.name, color[node.state], node.desc, node.name, tc_id_infobase, node_link, node.tc_id))

        if node.rmc:
            element.append('<img src="site/static/delete-icon.png">')
        if node.experr:
            element.append('<img src="site/static/beware.png">')
        if node.name in test_info:
            element.append("<a href='%stest_info/%s'><img src='site/static/info32.png'></a>" % (
                    base, node.name))
        #if node.mti == "MUST":
        #    element += '<img src="static/must.jpeg">'

    return "\n".join(element)

def test_target(tt_entityid):
    """
    Display the test target' entityID
    """
    return tt_entityid

%>

<%!

ICONS = [
    ('<img src="site/static/black.png" alt="Black">',"The test has not be run"),
    ('<img src="site/static/green.png" alt="Green">',"Success"),
    ('<img src="site/static/yellow.png" alt="Yellow">',
    "Warning, something was not as expected"),
    ('<img src="site/static/red.png" alt="Red">',"Failed"),
    ('<img src="site/static/qmark.jpg" alt="QuestionMark">',
    "The test flow wasn't completed. This may have been expected or not"),
    ('<img src="site/static/info32.png">',
    "Signals the fact that there are trace information available for the test"),
    ]

def legends():
    element = ["<table border='1' id='legends'>"]
    for icon, txt in ICONS:
        element.append("<tr><td>%s</td><td>%s</td></tr>" % (icon, txt))
    element.append('</table>')
    return "\n".join(element)
%>

<%
    def results(nodes, testresults):
        res = dict([(s, 0) for s in testresults.keys()])
        res[0] = 0
        tot = len(nodes)

        for node in nodes:
            res[node.state] += 1

        el = []
        for i in range(1, len(res)):
            el.append("<p>%s: %d</p>" % (testresults[i], res[i]))
        el.append("<p>Not run: %d</p>" % res[0])

        return "\n".join(el)
%>

<!DOCTYPE html>
<html>
<head>
    <title>SAML2 IdP Tests</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Bootstrap -->
    <link href="site/static/bootstrap/css/bootstrap.min.css" rel="stylesheet" media="screen">
    <link href="site/static/style.css" rel="stylesheet" media="all">

    <!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
    <script src="../../assets/js/html5shiv.js"></script>
    <script src="../../assets/js/respond.min.js"></script>
    <![endif]-->
    <style>
        @media (max-width: 768px) {
            .jumbotron {
                border-radius: 10px;
                margin-left: 4%;
                margin-right: 4%;
            }
        }
        @media (min-width: 768px) and (max-width: 1600px){
            .jumbotron {
                border-radius: 10px;
                margin-left: 10%;
                margin-right: 10%;
            }
        }
        @media (min-width: 1600px){
            .jumbotron {s
                border-radius: 10px;
                margin-left: 20%;
                margin-right: 20%;
            }
        }
    </style>
</head>
<body>
    <!-- Main component for a primary marketing message or call to action -->
    <div style="background-color: #4CAF50; color: #eee; width: 100%; height: 6em; vertical-align: middle; padding: .5em 2em .5em 2em">
        <h1>Federation Lab SAML2 IdP Tests</h1>
    </div>
    <div class="jumbotron" style="padding-left: 1em; padding-right: 2em">
        <h4>Test target: ${test_target(tt_entityid)}</h4>
        <em>Explanations of symbols at <a href="#legends">end of page</a></em>

        <h3>Chose the next test flow you want to run from this list: </h3>
        ${op_choice(base, flows, test_info, headlines, tc_id_infobase)}
        <hr style="heigth: 2px" />
        <h3>Legend</h3>
        ${legends()}
    </div>
    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="/site/static/jquery.min.1.9.1.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->
    <script src="/site/static/bootstrap/js/bootstrap.min.js"></script>

</body>
</html>