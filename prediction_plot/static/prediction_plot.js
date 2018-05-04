
line_color_map = {}

                function getRandomArbitrary(min, max) {
                    return Math.random() * (max - min) + min;
                }

                function InitChart(station, aq, period, plot_date) {
                    // create svg
                    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    svg.setAttribute('id', 'visualisation' + "_" + station + "_" + aq + "_" + period );
                    svg.setAttribute('width',1000);
                    svg.setAttribute('height',500);
                    $( ".jumbotron" ).append( svg );


d3.json("data_"+ plot_date +".json", function(data) {
                    // filter data
                    var arr = [] 
                    for( var i=0; i<data.length ;i++ ){
                        if( data[i]['station'] === station ) {
                            if (period === "short" && data[i]['offset'] === 24 ){
                                continue
                            }
                            if (period === "long" && data[i]['offset'] === 0 ){
                                continue
                            }

                            data[i]['hr'] = +data[i]['hr']
                            data[i]['O3'] = +data[i]['O3']
                            data[i]['pm25'] = +data[i]['pm25']
                            data[i]['pm10'] = +data[i]['pm10']
                         
                            arr.push(data[i])
                        } 
                    } 
                    data = arr
                    //console.log(data) 
                   
                    var dataGroup = d3.nest()
                        .key(function(d) {return d.Client;})
                        .entries(data);

//                    console.log(JSON.stringify(dataGroup));

                    var color = d3.scale.category10();

                    var vis = d3.select("#visualisation_"+station+"_"+aq+"_"+period ),
                        WIDTH = 1000,
                        HEIGHT = 500,
                        MARGINS = {
                            top: 50,
                            right: 20,
                            bottom: 50,
                            left: 50
                        },

                        //lSpace = WIDTH/dataGroup.length;
                        lSpace = WIDTH/4;

                        //console.log(data)
                        //var minX = d3.min(data, function(d) { return d.hr });
                        //var maxX = d3.max(data, function(d) { return d.hr });
                        //console.log(minX)
                        //console.log(maxX)
                        xScale = d3.scale.linear().range([MARGINS.left, WIDTH - MARGINS.right]).domain([d3.min(data, function(d) {
                            return d.hr;
                        }), d3.max(data, function(d) {
                            return d.hr;
                        })]),

                        //console.log(xScale)

                        yScale = d3.scale.linear().range([HEIGHT - MARGINS.top, MARGINS.bottom]).domain([d3.min(data, function(d) {
                            return d[aq];
                        }), d3.max(data, function(d) {
                            return d[aq];
                        })]),


                        xAxis = d3.svg.axis()
                        .scale(xScale),

                        yAxis = d3.svg.axis()
                        .scale(yScale)
                        .orient("left");

                    vis.append("svg:g")
                        .attr("class", "x axis")
                        .attr("transform", "translate(0," + (HEIGHT - MARGINS.bottom) + ")")
                        .call(xAxis);

                    vis.append("svg:g")
                        .attr("class", "y axis")
                        .attr("transform", "translate(" + (MARGINS.left) + ",0)")
                        .call(yAxis);

                    vis.append("text")
                        .attr("x", (WIDTH / 2))
                        .attr("y", (20))
                        .style("text-anchor", "middle")  
                        .style("font-size", "16px")
                        .style("text-decoration", "underline")  
                        .style("fill", "black")
                        .text( station+"_"+aq+"_"+period );
                        
                    var lineGen = d3.svg.line()
                        .x(function(d) {
                            return xScale(d.hr);
                        })
                        .y(function(d) {
                            return yScale(d[aq]);
                        })
                        .interpolate("basis");

                    dataGroup.forEach(function(d,i) {
                        if (!(d.key in line_color_map)) {
                            color_h = 0
                            color_s = 0.8
                            if (d.key !== "gt") {
                                color_h = getRandomArbitrary(70, 270)
                                color_s = getRandomArbitrary(0.2, 0.9)
                            }
                            line_color_map[d.key] = "hsl(" + color_h + "," + color_s*100 + "%,50%)"
                        }

                        line_color = line_color_map[d.key]

                        vis.append('svg:path')
                        .attr('d', lineGen(d.values))
                        .attr('stroke', function(d,j) { 
                                  return line_color;
                        })
                        .attr('stroke-width', 2)
                        .attr('id', 'line_'+d.key+"_"+station+"_"+aq+"_"+period)
                        .attr('fill', 'none');
                        
                        rect_size = 7
                        vis.append("rect")
                            .attr("x", (lSpace/3) + (i%4)*lSpace)
                            .attr("y", HEIGHT- (MARGINS.bottom/3) + Math.floor(i/4)*15 - rect_size )
                            .attr("width", rect_size)
                            .attr("height", rect_size)
                            .style("fill", function(d) {
                                  return line_color;
                            } )

                        vis.append("text")
                            .attr("x", (lSpace/3) + (i%4)*lSpace + rect_size*2)
                            .attr("y", HEIGHT- (MARGINS.bottom/3) + Math.floor(i/4)*15 )
                            .style("fill", "black")
                            .attr("class","legend")
                            .on('click',function(){
                                var active   = d.active ? false : true;
                                var opacity = active ? 0 : 1;

                                d3.select("#line_" + d.key +"_"+station+"_"+aq+"_"+period).style("opacity", opacity);

                                d.active = active;
                            })
                            .text(d.key.substring(0,25));
                    });

});
                    
                }

