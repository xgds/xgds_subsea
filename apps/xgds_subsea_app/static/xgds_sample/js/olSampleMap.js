// render json sample information on the openlayers map

var Sample = {
		selectedStylePath: '/static/xgds_sample/images/sample_icon_selected.png',
		stylePath: '/static/xgds_sample/images/sample_icon.png',
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                	zIndex: 1,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.stylePath,
                        scale: 0.8
                        }))
                      });
                this.styles['selectedIconStyle'] = new ol.style.Style({
                	zIndex: 10,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.selectedStylePath,
                        scale: 0.8
                        }))
                      });
                this.styles['yellowStroke'] =  new ol.style.Stroke({
                    color: 'yellow',
                    width: 2
                });
                this.styles['greenStroke'] =  new ol.style.Stroke({
                    color: 'green',
                    width: 2
                });
                this.styles['text'] = {
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke: this.styles['yellowStroke'],
                    offsetY: -15
                };
            }
        },
        constructElements: function(samplesJson){
            if (_.isEmpty(samplesJson)){
                return null;
            }
            this.initStyles();
            var olFeatures = [];
            for (var i = 0; i < samplesJson.length; i++) {
                if (samplesJson[i].lat !== "") {
                    var sampleFeature = this.constructMapElement(samplesJson[i]);
                    olFeatures = olFeatures.concat(sampleFeature);
                }
            }
            var vectorLayer = new ol.layer.Vector({
                name: samplesJson[0].type,
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(sampleJson){
            var coords = transform([sampleJson.lon, sampleJson.lat]);
            var feature = new ol.Feature({
            	selected: false,
            	view_url: '/xgds_map_server/view/' + sampleJson.type + '/' + sampleJson.pk,
                name: sampleJson.name,
                pk: sampleJson.pk,
                type: sampleJson.type,
                geometry: new ol.geom.Point(coords)
            });
            feature.setStyle(this.getStyles(sampleJson));
            this.setupPopup(feature, sampleJson);
            return feature;
        },
        getStyles: function(sampleJson) {
            var styles = [this.styles['iconStyle']];
            var theText = new ol.style.Text(this.styles['text']);
            theText.setText(sampleJson.name);
            var textStyle = new ol.style.Style({
                text: theText
            });
            styles.push(textStyle);
            return styles;
        },
        selectMapElement:function(feature){
        	feature.selected = false;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['selectedIconStyle']];
        	var newtextstyle = styles[1];
        	newtextstyle.getText().setStroke(this.styles['greenStroke']);
        	newtextstyle.setZIndex(10);
        	newstyles.push(newtextstyle);
        	feature.setStyle(newstyles);
        },
        deselectMapElement:function(feature){
        	feature.selected = true;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['iconStyle']];
        	var newtextstyle = styles[1];
        	newtextstyle.getText().setStroke(this.styles['yellowStroke']);
        	newtextstyle.setZIndex(1);
        	newstyles.push(newtextstyle);
        	feature.setStyle(newstyles);
        },
        setupPopup: function(feature, sampleJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (j = 0; j< 5; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            depthString = sprintf("%.3f m", sampleJson.depth)

            var data = ["Name:", sampleJson.name ? sampleJson.name : '',
                        "Type:", sampleJson.sample_type_name,
                        "Place:", sampleJson.place_name, //TODO: get label from settings
                        //"Time:", sampleJson.collection_time ? getLocalTimeString(sampleJson.collection_time, sampleJson.collection_timezone):'',
                        "Description:", sampleJson.description ? sampleJson.description : '',
                        "Depth:", depthString];
            var popupContents = vsprintf(formattedString, data);
            feature['popup'] = popupContents;
        }
}