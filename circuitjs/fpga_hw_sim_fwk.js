// get iframe the simulator is running in.  Must have same origin as this file!
var iframe = document.getElementById("circuitFrame");


// ########################################################
var socket = null;
var isopen = false;

window.onload = function() {

   socket = new WebSocket("ws://127.0.0.1:9000");
   socket.binaryType = "arraybuffer";

   socket.onopen = function() {
      console.log("Connected!");
      isopen = true;
   }

   socket.onmessage = function(e) {
      if (typeof e.data == "string") {
         console.log("Text message received: " + e.data);
         // set switch
         if (e.data == "True"){
          sim.setExtVoltage("ext", 5.0);          
         } else {
          sim.setExtVoltage("ext", 0.0);
         }
      }
   }

   socket.onclose = function(e) {
      console.log("Connection closed.");
      socket = null;
      isopen = false;
   }
};
// ########################################################


var sim;
var freq, ampl;
var elmList = [];
var elm_d0; // value sent to python app over websocket
var elm_d0_voltage_temp = 0;
var elm_switch; // set by python app over websocket


function round(x) {
  return Math.round(x*1000)/1000;
}

// called when simulator updates its display
function didUpdate(sim) {
  var info = document.getElementById("info");
  info.innerHTML = "time = " + round(sim.getTime()) + "<br>running = " + sim.isRunning();

  // get voltage of labeled node "vsense"
  var vsense = sim.getNodeVoltage("vsense");
  info.innerHTML += "<br>V(vsense) = " + round(vsense);

  freq = parseFloat(document.getElementById("freq").value);
  ampl = parseFloat(document.getElementById("ampl").value);

  var bstr = "";
  var bval = 0;
  var i;
  for (i = 7; i >= 0; i--) {
    var v = sim.getNodeVoltage("D" + i);
    if (v > 2.5) {
      bstr += "1";
      bval = 2*bval+1;
    } else {
      bstr += "0";
      bval = 2*bval;
    }
  }
  info.innerHTML += "<br>counter value = <tt>" + bstr + "</tt> = " + bval;

  var rcount = 0;

  // go through list of elements
  for (const elm of elmList) {
    if (elm.getType() == "ResistorElm") {
      // show info about each resistor
      rcount++;
      info.innerHTML += "<br>resistor " + rcount + " voltage diff = " + round(elm.getVoltageDiff());
      info.innerHTML += "<br>resistor " + rcount + " current = " + round(elm.getCurrent() * 1000) + " mA";
    } else if (elm.getType() == "LabeledNodeElm") {
      // show voltage of each labeled node
      info.innerHTML += "<br>V(" + elm.getLabelName() + ") = " + round(elm.getVoltage(0));
    }
  }
}

// called when simulator analyzes a circuit (when a circuit is loaded or edited)
function didAnalyze(sim) {
  console.log("analyzed circuit");

  // get the list of elements
  elmList = sim.getElements();

  // log some info about each one
  for (const elm of elmList) {
    console.log("elm " + elm.getType() + ", " + elm.getPostCount() + " posts");
    console.log("elm info: " + elm.getInfo());
    // initialize variables updated over websocket
    if (elm.getType() == "LabeledNodeElm") {
      if (elm.getLabelName() == "D0") {
        elm_d0 = elm;
      }
    }
    else if (elm.getType() == "SwitchElm") {
      elm_switch = elm;
    }
  }
}

// called every timestep
function didStep(sim) {
  // send new value to python app over websocket
  var curr_voltage = elm_d0.getVoltage(0)
  if (curr_voltage != elm_d0_voltage_temp) {
    if (isopen) {
      socket.send(round(curr_voltage));
      elm_d0_voltage_temp = curr_voltage;
    }
  }
}

// callback called when simulation is done initializing
function simLoaded() {
  // get simulator object
  sim = iframe.contentWindow.CircuitJS1;

  // set up callbacks on update and timestep
  sim.onupdate = didUpdate;
  sim.ontimestep = didStep;
  sim.onanalyze = didAnalyze;
}

// set up callback
iframe.contentWindow.oncircuitjsloaded = simLoaded;
