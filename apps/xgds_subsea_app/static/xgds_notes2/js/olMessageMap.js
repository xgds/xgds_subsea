// render json message information on the openlayers map

String.prototype.trunc = String.prototype.trunc ||
      function(n){
          return (this.length > n) ? this.substr(0, n-1) : this;
      };

var Message = {
		selectedStylePath: '/static/xgds_notes2/icons/comment2_selected.png',
		stylePath: '/static/xgds_notes2/icons/comment2.png',
        initStyles: function() {
            if (_.isUndefined(this.styles)){
                this.styles = {};
                this.styles['iconStyle'] = new ol.style.Style({
                	zIndex: 1,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.stylePath,
                        }))
                      });
                this.styles['selectedIconStyle'] = new ol.style.Style({
                	zIndex: 10,
                    image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
                        src: this.selectedStylePath,
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
                	zIndex: 1,
                    font: '12px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: 'black'
                    }),
                    stroke: this.styles['yellowStroke'],
                    offsetY: -15
                };
            }
        },
        constructElements: function(messagesJson){
            if (_.isEmpty(messagesJson)){
                return null;
            }
            this.initStyles();
            var olFeatures = [];
            for (var i = 0; i < messagesJson.length; i++) {
                if (_.isNumber(messagesJson[i].lat)) {
                    var messageFeature = this.constructMapElement(messagesJson[i]);
                    olFeatures = olFeatures.concat(messageFeature);
                }
            }
            var vectorLayer = new ol.layer.Vector({
                name: messagesJson[0].type,
                source: new ol.source.Vector({
                    features: olFeatures
                }),
            });  
            return vectorLayer;
        },
        constructMapElement:function(messageJson){
            var coords = transform([messageJson.lon, messageJson.lat]);
            var view_url = messageJson.content_url;
            var feature = new ol.Feature({
            	selected: false,
                name: getLocalTimeString(messageJson.event_time, messageJson.event_timezone),
                uuid: messageJson.pk,
                pk: messageJson.pk,
                type: messageJson.type,
                geometry: new ol.geom.Point(coords)
            });
            feature.setStyle(this.getStyles(messageJson));
            this.setupPopup(feature, messageJson);
            return feature;
        },
        getStyles: function(messageJson) {
            var styles = [this.styles['iconStyle']];
            return styles;
        },
        selectMapElement:function(feature){
        	feature.selected = false;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['selectedIconStyle']];
        	feature.setStyle(newstyles);
        },
        deselectMapElement:function(feature){
        	feature.selected = true;
        	var styles = feature.getStyle();
        	var newstyles = [this.styles['iconStyle']];
        	feature.setStyle(newstyles);
        },
        setupPopup: function(feature, messageJson) {
            var trString = "<tr><td>%s</td><td>%s</td></tr>";
            var formattedString = "<table>";
            for (j = 0; j< 3; j++){
                formattedString = formattedString + trString;
            }
            formattedString = formattedString + "</table>";
            depthString = sprintf("%.3f m", messageJson.depth)

            var data = ["Author:", messageJson.author_name,
                        "Message:", messageJson.content,
                        "Depth:", depthString];
            var popupContents = vsprintf(formattedString, data);
            feature['popup'] = popupContents;
        		
        }
}