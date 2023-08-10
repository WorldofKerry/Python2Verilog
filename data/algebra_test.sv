module tb();
  reg signed [31:0] x;
  reg signed [31:0] y;
  reg signed [31:0] z;

  initial begin
    x = -3;
    y = 7;

//     z = (x >= $signed(0)) ? (x / y) : (x / (y - $signed(-1)));
//     z = x / (y - 50);
//     z = x / y >= $signed(0) ? x / y : x / y - 1;
    z = x / y >= $signed(0) ? x % y : -(x % y);

    $display("%d %d %d", x, y, z);

  end
endmodule
