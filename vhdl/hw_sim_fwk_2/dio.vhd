library ieee;
use ieee.std_logic_1164.ALL;
use ieee.numeric_std.all;


entity dio is
    generic(
        NR_DIS      : integer := 2;
        NR_DIS_SYNC : integer := NR_DIS/2;
        NR_DOS      : integer := 2
    );
    port(
        reset  : in  std_logic;
        clock  : in  std_logic;
        di     : in  std_logic_vector(NR_DIS - 1 downto 0);        
        do     : out std_logic_vector(NR_DOS - 1 downto 0);
        led    : out std_logic
    );
end dio;

architecture Behavioral of dio is
    -- Set USE_PROCESS_LOGIC to use process logic or just wire-through
    -- With wire-through we avoid using an additional register which also adds a new delay.
    -- But in case some additional logic is needed we do need this additional intermediate step.
    constant USE_PROCESS_LOGIC : boolean := true; -- false;
    -- TODO: check these parameters!
    constant NR_SAMPLES : integer := 14;
    constant MAX_NR_TICKS : integer := 280 - 14;
    constant DI_THRESHOLD : integer := 400; -- TODO: change e.g. to 800
    signal do_reg : std_logic_vector(NR_DOS - 1 downto 0);
    signal led_reg : std_logic;
begin
    g_conditional_process : if USE_PROCESS_LOGIC = true generate
        -- process DIs, DOs
        -- ################
        -- NOTE: the di signal is "partially" inside the sensitivity list so we support "asynchronous" DIs for the "upper" DIs
        proc_dio : process(reset, clock, di(NR_DIS - 1 downto NR_DIS_SYNC))
            variable di_last : std_logic_vector(NR_DIS - 1 downto 0); -- to track async signal
            type int_array is array(0 to NR_SAMPLES-1) of integer;
            variable di_int_array : int_array;
            variable di_int_last : integer;
            variable di_int_max : integer;
            variable sample_pos : integer;
            variable clk_ticks : integer;
        begin
            -- asynchronous reset 
            if (reset = '1') then
                do_reg <= (others => '0');
                led_reg <= '0';
                clk_ticks := 0;
                sample_pos := 0;
                di_int_max := 0;
            -- asynchronous DIs that might as well be output as asynchronous DOs
            elsif (di /= di_last) then
                do_reg <= di;
                di_last := di;
            -- synchronous events
            elsif rising_edge(clock) then                
                do_reg <= di;
                di_last := di;                
                -- detect decrease in signal
                if clk_ticks < MAX_NR_TICKS then
                    clk_ticks := clk_ticks + 1;
                else
                    if (to_integer(unsigned(di)) /= di_int_last) then
                        di_int_array(sample_pos) := to_integer(unsigned(di));
                        di_int_last := di_int_array(sample_pos); 
                        -- report("di_int[" &integer'image(sample_pos) &"] = " &integer'image(di_int_array(sample_pos)));
                        sample_pos := sample_pos + 1;
                        if (sample_pos = NR_SAMPLES) then
                            for i in 0 to NR_SAMPLES-1 loop                            
                                if (di_int_max < di_int_array(i)) then
                                    di_int_max := di_int_array(i);
                                end if;
                            end loop;
                            if (di_int_max < DI_THRESHOLD) then
                                -- report("detection!");
                                led_reg <= '1';
                            else
                                led_reg <= '0';
                            end if;
                            sample_pos := 0;
                            clk_ticks := 0;
                            di_int_max := 0;
                        end if;
                    end if;
                end if;               
            end if;
        end process proc_dio;
        -- output signals
        -- ##############
        do <= do_reg;
        led <= led_reg;
    end generate g_conditional_process;
    -- Note: the "else generate" construct is only supported in VHDL 1076-2008
    --       so we use a separate (and complementary) generate condition
    g_conditional_wirethrough : if USE_PROCESS_LOGIC = false generate
        do <= di;
    end generate g_conditional_wirethrough;
end Behavioral;

