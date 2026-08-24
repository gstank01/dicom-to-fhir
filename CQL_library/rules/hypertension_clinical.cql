library hypertension_clinical version '1.0.0'

using FHIR version '4.0.1'

include FHIRHelpers version '4.0.1'

context Patient

define SystolicHigh:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '85354-9') // BP panel
        and exists (O.component Comp
          where exists (Comp.code.coding Cc where Cc.code = '8480-6') // Systolic
            and (FHIRHelpers.ToQuantity(Comp.value)).value >= 140
        )
  )

define DiastolicHigh:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '85354-9') // BP panel
        and exists (O.component Comp
          where exists (Comp.code.coding Cc where Cc.code = '8462-4') // Diastolic
            and (FHIRHelpers.ToQuantity(Comp.value)).value >= 91
        )
  )

define IVSD_Thickened:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '76400-1')
        and (FHIRHelpers.ToQuantity(O.value)).value >= 13
  )

define PWd_Thickened:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '76403-5')
        and (FHIRHelpers.ToQuantity(O.value)).value >= 12
  )

define LAE:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '8618-1')
        and (FHIRHelpers.ToQuantity(O.value)).value >= 40
  )

define LVMI_High:
  exists (
    [Observation] O
      where exists (O.code.coding C where C.code = '76482-9')
        and (
          (Patient.gender = 'male' and (FHIRHelpers.ToQuantity(O.value)).value > 115) or
          (Patient.gender = 'female' and (FHIRHelpers.ToQuantity(O.value)).value > 95)
        )
  )

define EchoSigns:
  IVSD_Thickened and PWd_Thickened and LAE and LVMI_High

define Hypertension:
  (SystolicHigh or DiastolicHigh) and EchoSigns
