module happy_face_tb;
    // Inputs
    reg _clock;
    reg _start;
      reg signed [31:0] radius;

  // Outputs
  wire signed [31:0] _out0;
  wire signed [31:0] _out1;

    wire _done;
    wire _valid;

    // Instantiate the module under test
    happy_face dut (
    ._clock(_clock),
    ._start(_start),
        .radius(radius),
    ._out0(_out0),
    ._out1(_out1),

    ._done(_done),
    ._valid(_valid)
    );

    // Clock generation
    always #5 _clock = !_clock;

    // Stimulus
    initial begin
    // Initialize inputs
    _start = 0;
        radius = 5;

    _clock = 0;

    // Wait for a few clock cycles
    #10;

    // Start the drawing process
    @(posedge _clock);
    _start = 1;
    @(posedge _clock);

    // Wait for the drawing to complete
    while (!_done) begin
    @(posedge _clock);
    _start = 0;
    // Display the outputs for every cycle after start
    $display("%0d, %0d, %0d", _valid, _out0, _out1);

    end

    // Finish simulation
    $finish;
    end

    endmodule
