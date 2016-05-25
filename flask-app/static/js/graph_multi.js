$(function () {

    $(document).ready(function() {


        var countiesMap = Highcharts.geojson(Highcharts.maps['countries/us/us-all-all']);
        var lines = Highcharts.geojson(Highcharts.maps['countries/us/us-all-all'], 'mapline');


        var county_map = new Highcharts.Map({
            chart: {renderTo: 'county_map',

                    events: { load: function () {
                                var seriesData = this.series[0];

                                setInterval(function () {
                                    $.ajax({ type: "GET",
                                         url: '/update_map/',
                                         success: function(data) {
                                            seriesData.setData(data.rt_data);
                                         }
                                    })
                                }, 3000);


                            }
                        }},
            title : { text : 'Current Messages by County' },
            legend: { title: { text: '# of Messages',
                               style: { color: (Highcharts.theme && Highcharts.theme.textColor) || 'black' } },
                               layout: 'vertical',
                               align: 'right',
                               floating: true,
                               valueDecimals: 0,
                               backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || 'rgba(255, 255, 255, 0.85)',
                               symbolRadius: 0,
                               symbolHeight: 14 },
            mapNavigation: { enabled: true,
                             enableMouseWheelZoom: false},
            colorAxis: { dataClasses: [{ from: 0, to: 2, color: "#ffffcc" },
                                       { from: 2, to: 4, color: "#ffeda0" },
                                       { from: 4, to: 6, color: "#fed976" },
                                       { from: 6, to: 8, color: "#feb24c" },
                                       { from: 8, to: 12, color: "#fd8d3c" },
                                       { from: 12, to: 20, color: "#fc4e2a" },
                                       { from: 20, to: 36, color: "#e31a1c" },
                                       { from: 36, to: 58, color: "#bd0026" },
                                       { from: 58, color: "#800026" }] },
            plotOptions: { mapline: { showInLegend: false, enableMouseTracking: false },
                           series: { cursor: 'pointer',
                                     allowPointSelect: true,
                                     marker: { lineWidth: 1 }

                                    }
                          },
            series : [{mapData : countiesMap,
                       data: null,
                       joinBy: ['hc-key', 'code'],
                       name: '# of Messages',
                       borderWidth: 0.5,
                       states: { hover: { color: '#bada55' } } },
                      {type: 'mapline',
                       name: 'State borders',
                       data: [lines[0]],
                       color: 'black' },
                      {type: 'mapline',
                       name: 'Separator',
                       data: [lines[1]],
                       color: 'gray' }]
	    });

	});
});
