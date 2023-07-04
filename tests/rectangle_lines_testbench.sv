module draw_rectangle_tb;

  // Inputs
  reg _clock;
  reg _start;
  reg [31:0] s_x;
  reg [31:0] s_y;
  reg [31:0] height;
  reg [31:0] width;

  // Outputs
  wire [31:0] __out0;
  wire [31:0] __out1;
  wire _done;

  // Instantiate the module under test
  draw_rectangle dut (
    ._clock(_clock),
    ._start(_start),
    .s_x(s_x),
    .s_y(s_y),
    .height(height),
    .width(width),
    ._out0(__out0),
    ._out1(__out1),
    ._done(_done)
  );

  // Clock generation
  always #5 _clock = !_clock;

  // Stimulus
  initial begin
    // Initialize inputs
    _start = 0;
    s_x = 1;
    s_y = 2;
    height = 3;
    width = 4;
    _clock = 0; 

    // Wait for a few clock cycles
    #10;

    // Start the drawing process
    @(posedge _clock);
    _start = 1;

    // Wait for the drawing to complete
    repeat (30) begin
      @(posedge _clock);
      _start = 0; 
      // Display the outputs for every cycle after start
      $display("%0d, %0d, %0d, %0d", $time, __out0, __out1, _done);
    end 
    
    // Finish simulation
    $finish;
  end

endmodule
